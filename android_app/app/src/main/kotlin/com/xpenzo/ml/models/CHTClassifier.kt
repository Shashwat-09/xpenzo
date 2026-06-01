package com.xpenzo.ml.models

import android.content.Context
import android.util.Log
import com.xpenzo.ml.core.ClassificationResult
import com.xpenzo.ml.core.ClassificationSource
import com.xpenzo.ml.core.ClassifierInput
import com.xpenzo.ml.core.TransactionClassifier
import com.xpenzo.ml.manager.BundledModelAssets
import java.io.File
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.tensorflow.lite.Interpreter
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.ln
import kotlin.math.sin
import kotlin.system.measureTimeMillis

class CHTClassifier(
    private val context: Context,
    private val tfliteAsset: String = BundledModelAssets.tfliteModel,
    private val spAsset: String = BundledModelAssets.tokenizerModel,
) : TransactionClassifier {
    override val displayName = "CHT 520-Class Neural Model"
    override val version = "5.0-canonical"
    override val modelSizeBytes = 5_130_256L
    override val supportsColdStart = true

    private var interpreter: Interpreter? = null
    private var l1Labels: Array<String> = emptyArray()
    private var l2Labels: Array<String> = emptyArray()
    private var l3Labels: Array<String> = emptyArray()
    private var tokenizer: SentencePieceTokenizer? = null

    override suspend fun warmUp(): Unit = withContext(Dispatchers.IO) {
        if (interpreter != null) return@withContext

        interpreter = Interpreter(loadModelBuffer(tfliteAsset))
        l1Labels = loadLabels(BundledModelAssets.l1Labels)
        l2Labels = loadLabels(BundledModelAssets.l2Labels)
        l3Labels = loadLabels(BundledModelAssets.l3Labels)
        tokenizer = loadTokenizer()
        Log.i("CHTClassifier", "Warmed up. vocab=${tokenizer?.vocabSize} l1=${l1Labels.size} l2=${l2Labels.size} l3=${l3Labels.size}")
    }

    override fun close() {
        interpreter?.close()
        interpreter = null
        tokenizer = null
    }

    private fun loadTokenizer(): SentencePieceTokenizer? = runCatching {
        val bytes = context.assets.open(spAsset).readBytes()
        SentencePieceTokenizer(bytes)
    }.getOrElse {
        Log.w("CHTClassifier", "Could not load SentencePiece tokenizer from $spAsset", it)
        null
    }

    override suspend fun classify(input: ClassifierInput): ClassificationResult =
        withContext(Dispatchers.Default) {
            val activeInterpreter = interpreter ?: error("Call warmUp() before classify().")
            lateinit var result: ClassificationResult
            val elapsed = measureTimeMillis {
                val tokenIds = prepareTextInput(input)
                val numericFeatures = prepareNumericalFeatures(input)
                val l1Output = Array(1) { FloatArray(l1Labels.size.coerceAtLeast(1)) }
                val l2Output = Array(1) { FloatArray(l2Labels.size.coerceAtLeast(1)) }
                val l3Output = Array(1) { FloatArray(l3Labels.size.coerceAtLeast(1)) }

                val outputs = mutableMapOf<Int, Any>(
                    0 to l1Output,
                    1 to l2Output,
                    2 to l3Output,
                )

                activeInterpreter.runForMultipleInputsOutputs(
                    arrayOf(arrayOf(tokenIds), arrayOf(numericFeatures)),
                    outputs,
                )

                val l1Index = l1Output[0].argmax()
                val l2Index = l2Output[0].argmax()
                val topIndices = l3Output[0].topIndices(limit = 3)
                result = ClassificationResult(
                    l1Category = l1Labels.getOrElse(l1Index) { "Others" },
                    l1Confidence = l1Output[0].getOrElse(l1Index) { 0f },
                    l2Category = l2Labels.getOrElse(l2Index) { "Miscellaneous" },
                    l2Confidence = l2Output[0].getOrElse(l2Index) { 0f },
                    l3Category = l3Labels.getOrElse(topIndices.firstOrNull() ?: 0) { "Miscellaneous" },
                    l3Confidence = topIndices.firstOrNull()?.let { l3Output[0].getOrElse(it) { 0f } } ?: 0f,
                    top3 = topIndices.map { index -> l3Labels.getOrElse(index) { "Unknown" } to l3Output[0][index] },
                    source = ClassificationSource.ML_MODEL,
                )
            }
            result.copy(inferenceMs = elapsed)
        }

    /**
     * Tokenize the normalized merchant text using the bundled SentencePiece BPE model.
     *
     * CONTRACT — input.merchantName must already be the NORMALIZED text produced by
     * [UpiSmsParser.normalizeMerchant] (lowercase, digits KEPT, special chars→space,
     * deduped spaces). That normalization matches the Python `text_normalized` column
     * (10_feature_engineering.py::normalize_merchant) exactly — digits are NOT hashed here;
     * masking happens only on the ml_corrections upload path.
     *
     * If the tokenizer is unavailable (e.g. first cold-start before warmUp completes),
     * falls back to BOS+PAD sequence so at least the output tensor shape is correct.
     */
    private fun prepareTextInput(input: ClassifierInput): IntArray {
        val tok = tokenizer
        val text = canonicalTextField(input)

        if (tok == null) {
            Log.w("CHTClassifier", "Tokenizer not loaded — returning pad sequence")
            return IntArray(sequenceLength) { if (it == 0) bosId else padId }
        }

        return tok.encode(text, sequenceLength)
    }

    /**
     * Returns the single normalized text field that the 520-class model was trained on.
     *
     * Rule: use [ClassifierInput.merchantName] (which callers must pre-normalize via
     * [UpiSmsParser.normalizeMerchant]). Only fall back to the VPA prefix if the
     * merchant is blank — never use raw SMS body as the model input.
     */
    private fun canonicalTextField(input: ClassifierInput): String {
        return when {
            input.merchantName.isNotBlank() -> input.merchantName
            input.upiId.isNotBlank() -> input.upiId.substringBefore("@")
            else -> "unknown"
        }
    }

    /**
     * Canonical 16-dim numerical feature vector.
     *
     * PARITY CONTRACT — must match Python:
     *   ml/data_collection/scripts/10_feature_engineering.py::compute_numerical_features()
     * and ml/retrain.py::compute_numerical_features().
     *
     * Key invariants:
     *   [0]  log(amount_rupees + 1)
     *   [1]  amountBucket as raw int 0–10  (NOT divided by 10 — training used 5.0, not 0.5)
     *   [2]  is_round (1.0 if amount > 0 and divisible by 10)
     *   [3-4] sin/cos of hour of day
     *   [5-6] sin/cos of day of week (0=Mon … 6=Sun)
     *   [7]  is_weekend
     *   [8]  is_meal_hour (11–14 or 19–22)
     *   [9]  is_salary_window (day 1–5 of month)
     *   [10-11] sin/cos of month
     *   [12] is_holiday (always 0 — not computed on device)
     *   [13] has_location (1.0 if lat/lon provided)
     *   [14] lat_normalized = (lat - 6.0) / 31.0  (India bounding box)
     *   [15] lon_normalized = (lon - 68.0) / 29.5
     */
    private fun prepareNumericalFeatures(input: ClassifierInput): FloatArray {
        val hour = input.timestamp.hour
        val dayOfWeek = input.timestamp.dayOfWeek.value - 1  // 0=Mon … 6=Sun
        val month = input.timestamp.monthValue
        val dayOfMonth = input.timestamp.dayOfMonth

        val amountBucket: Int = when {
            input.amount < 50 -> 0
            input.amount < 100 -> 1
            input.amount < 200 -> 2
            input.amount < 500 -> 3
            input.amount < 1_000 -> 4
            input.amount < 2_000 -> 5
            input.amount < 5_000 -> 6
            input.amount < 10_000 -> 7
            input.amount < 25_000 -> 8
            input.amount < 50_000 -> 9
            else -> 10
        }

        val hasLocation = input.latitude != null && input.longitude != null
        val latNorm = if (hasLocation) ((input.latitude!! - LAT_MIN) / (LAT_MAX - LAT_MIN)).toFloat().coerceIn(0f, 1f) else 0f
        val lonNorm = if (hasLocation) ((input.longitude!! - LON_MIN) / (LON_MAX - LON_MIN)).toFloat().coerceIn(0f, 1f) else 0f

        return floatArrayOf(
            ln(input.amount + 1).toFloat(),        // [0] log(amount + 1)
            amountBucket.toFloat(),                 // [1] raw bucket 0–10 (NOT /10)
            if (input.amount > 0 && input.amount % 10 == 0.0) 1f else 0f, // [2] is_round
            sin(2 * PI * hour / 24).toFloat(),     // [3] hour_sin
            cos(2 * PI * hour / 24).toFloat(),     // [4] hour_cos
            sin(2 * PI * dayOfWeek / 7).toFloat(), // [5] dow_sin
            cos(2 * PI * dayOfWeek / 7).toFloat(), // [6] dow_cos
            if (dayOfWeek >= 5) 1f else 0f,        // [7] is_weekend
            if (hour in 11..14 || hour in 19..22) 1f else 0f, // [8] is_meal_hour
            if (dayOfMonth in 1..5) 1f else 0f,   // [9] is_salary_window
            sin(2 * PI * month / 12).toFloat(),    // [10] month_sin
            cos(2 * PI * month / 12).toFloat(),    // [11] month_cos
            0f,                                     // [12] is_holiday
            if (hasLocation) 1f else 0f,            // [13] has_location
            latNorm,                                // [14] lat_normalized
            lonNorm,                                // [15] lon_normalized
        )
    }

    private fun assetExists(path: String): Boolean =
        runCatching {
            context.assets.open(path).close()
            true
        }.getOrDefault(false)

    private fun loadModelBuffer(assetOrPath: String): ByteBuffer {
        val file = File(assetOrPath)
        return if (file.exists()) {
            FileInputStream(file).channel.map(FileChannel.MapMode.READ_ONLY, 0, file.length())
        } else {
            val descriptor = context.assets.openFd(assetOrPath)
            FileInputStream(descriptor.fileDescriptor).channel.map(
                FileChannel.MapMode.READ_ONLY,
                descriptor.startOffset,
                descriptor.declaredLength,
            )
        }
    }

    private fun loadLabels(assetName: String): Array<String> =
        runCatching {
            context.assets.open(assetName).bufferedReader().readLines().toTypedArray()
        }.getOrElse {
            Log.w("CHTClassifier", "Missing label asset $assetName; using placeholder labels.")
            arrayOf("Miscellaneous")
        }

    private fun FloatArray.argmax(): Int = indices.maxByOrNull { this[it] } ?: 0

    private fun FloatArray.topIndices(limit: Int): List<Int> =
        indices.sortedByDescending { this[it] }.take(limit)

    private companion object {
        const val sequenceLength = 32
        const val padId = 0
        const val bosId = 2
        const val eosId = 3

        // India bounding box for lat/lon normalization (matches 10_feature_engineering.py)
        const val LAT_MIN = 6.0
        const val LAT_MAX = 37.0
        const val LON_MIN = 68.0
        const val LON_MAX = 97.5
    }
}
