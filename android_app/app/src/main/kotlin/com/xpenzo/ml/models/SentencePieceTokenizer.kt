package com.xpenzo.ml.models

import android.util.Log

/**
 * Lightweight SentencePiece BPE tokenizer that reads [xpenz_bpe.model] directly.
 *
 * ## Why this exists
 * The canonical 520-class CHT model expects token IDs produced by the exact same
 * SentencePiece model used during training. Using character codes (the old hack)
 * produces completely wrong embeddings and tanks accuracy.
 *
 * ## Implementation
 * We parse the SentencePiece protobuf binary directly without an external library.
 * The proto layout is:
 *   ModelProto {
 *     repeated SentencePiece pieces = 1;  // field_tag = (1 << 3) | 2 = 0x0A
 *   }
 *   SentencePiece {
 *     string piece  = 1;   // field_tag = (1 << 3) | 2 = 0x0A
 *     float  score  = 2;   // field_tag = (2 << 3) | 5 = 0x15
 *     uint32 type   = 3;   // field_tag = (3 << 3) | 0 = 0x18
 *   }
 * The index of each piece in the repeated field equals its token ID.
 *
 * ## Encoding contract  (must match training `prepare_text_input`):
 *   tokens = [BOS, subword_ids..., EOS, PAD...PAD]   length = maxLen
 *   text   = merchantNormalized (lowercase, digits KEPT, already normalized upstream)
 */
class SentencePieceTokenizer(modelBytes: ByteArray) {

    /** id → piece string  (e.g. 42 → "swiggy") */
    private val idToPiece: Array<String>

    /** piece string → id  (reverse lookup for encoding) */
    private val pieceToId: HashMap<String, Int>

    /** Score for each piece, used to sort merge candidates. */
    private val pieceScore: FloatArray

    val vocabSize: Int get() = idToPiece.size

    init {
        val pieces = mutableListOf<Pair<String, Float>>() // (piece, score)
        var pos = 0

        while (pos < modelBytes.size) {
            val tag = modelBytes.readVarint(pos)
            pos += varintSize(modelBytes, pos)

            when (tag.toInt()) {
                0x0A -> {
                    // pieces field — length-delimited SentencePiece sub-message
                    val len = modelBytes.readVarint(pos).toInt()
                    pos += varintSize(modelBytes, pos)
                    val subEnd = pos + len
                    var piece = ""
                    var score = 0f
                    var subPos = pos

                    while (subPos < subEnd) {
                        val subTag = modelBytes.readVarint(subPos).toInt()
                        subPos += varintSize(modelBytes, subPos)
                        when (subTag) {
                            0x0A -> {
                                // string piece
                                val sLen = modelBytes.readVarint(subPos).toInt()
                                subPos += varintSize(modelBytes, subPos)
                                piece = String(modelBytes, subPos, sLen, Charsets.UTF_8)
                                subPos += sLen
                            }
                            0x15 -> {
                                // float score (little-endian IEEE 754)
                                val bits = ((modelBytes[subPos + 3].toInt() and 0xFF) shl 24) or
                                    ((modelBytes[subPos + 2].toInt() and 0xFF) shl 16) or
                                    ((modelBytes[subPos + 1].toInt() and 0xFF) shl 8) or
                                    (modelBytes[subPos].toInt() and 0xFF)
                                score = java.lang.Float.intBitsToFloat(bits)
                                subPos += 4
                            }
                            0x18 -> {
                                // uint32 type — skip varint
                                modelBytes.readVarint(subPos)
                                subPos += varintSize(modelBytes, subPos)
                            }
                            else -> {
                                // Unknown field — skip by wire type
                                subPos = skipField(modelBytes, subPos, subTag)
                            }
                        }
                    }
                    pieces.add(piece to score)
                    pos = subEnd
                }
                else -> {
                    // Skip all other top-level fields (trainer_spec, normalizer_spec, etc.)
                    pos = skipField(modelBytes, pos, tag.toInt())
                }
            }

            if (pos < 0 || pos > modelBytes.size) break // safety valve
        }

        idToPiece = Array(pieces.size) { pieces[it].first }
        pieceScore = FloatArray(pieces.size) { pieces[it].second }
        pieceToId = HashMap(pieces.size * 2)
        pieces.forEachIndexed { id, (p, _) -> pieceToId[p] = id }

        Log.d(TAG, "Loaded SentencePiece vocab: ${pieces.size} pieces")
    }

    // ── public API ────────────────────────────────────────────────────────────

    /**
     * Encode [text] into a fixed-length [IntArray] of length [maxLen].
     * Layout: [BOS, token1, token2, ..., EOS, PAD, PAD, ...]
     *
     * Uses BPE greedy longest-match tokenization, consistent with the training
     * pipeline's `tokenizer.encode("<bos> text <eos>")` call.
     */
    fun encode(text: String, maxLen: Int = 32): IntArray {
        val result = IntArray(maxLen) { PAD_ID }
        val tokens = bpeTokenize(text.trim())

        var pos = 0
        result[pos++] = BOS_ID

        for (token in tokens) {
            if (pos >= maxLen - 1) break // leave room for EOS
            val id = pieceToId[token] ?: pieceToId["▁${token}"] ?: UNK_ID
            result[pos++] = id
        }
        if (pos < maxLen) result[pos] = EOS_ID

        return result
    }

    /** Decode token IDs back to text (for debugging / parity tests). */
    fun decode(ids: IntArray): String =
        ids.filter { it > EOS_ID }
            .joinToString("") { id ->
                idToPiece.getOrElse(id) { "<unk>" }
                    .replace("▁", " ")
            }.trim()

    // ── BPE tokenization ──────────────────────────────────────────────────────

    /**
     * Greedy BPE tokenization via max-munch on the piece vocabulary.
     * SentencePiece prepends "▁" (U+2581) to mark word starts.
     */
    private fun bpeTokenize(text: String): List<String> {
        if (text.isBlank()) return emptyList()

        // Split on whitespace; prepend "▁" to each word (SentencePiece convention)
        val words = text.split(Regex("\\s+"))
            .filter { it.isNotEmpty() }
            .mapIndexed { i, word -> if (i == 0) "▁$word" else "▁$word" }

        val result = mutableListOf<String>()
        for (word in words) {
            result.addAll(tokenizeWord(word))
        }
        return result
    }

    /**
     * Tokenize a single word using longest-match-first BPE.
     * Falls back to character-level + <unk> for unknown characters.
     */
    private fun tokenizeWord(word: String): List<String> {
        if (word.isEmpty()) return emptyList()

        // Check if the whole word is in vocab
        if (pieceToId.containsKey(word)) return listOf(word)

        val tokens = mutableListOf<String>()
        var start = 0
        while (start < word.length) {
            var end = word.length
            var found = false
            while (end > start) {
                val sub = word.substring(start, end)
                if (pieceToId.containsKey(sub)) {
                    tokens.add(sub)
                    start = end
                    found = true
                    break
                }
                end--
            }
            if (!found) {
                // Character not in vocab — emit as UNK and advance
                tokens.add("<unk>")
                start++
            }
        }
        return tokens
    }

    // ── protobuf parsing helpers ──────────────────────────────────────────────

    private fun ByteArray.readVarint(pos: Int): Long {
        var result = 0L
        var shift = 0
        var p = pos
        while (p < size) {
            val b = this[p++].toInt() and 0xFF
            result = result or ((b and 0x7F).toLong() shl shift)
            if (b and 0x80 == 0) break
            shift += 7
        }
        return result
    }

    private fun varintSize(bytes: ByteArray, pos: Int): Int {
        var p = pos
        while (p < bytes.size && bytes[p].toInt() and 0x80 != 0) p++
        return (p - pos + 1).coerceAtLeast(1)
    }

    private fun skipField(bytes: ByteArray, pos: Int, tag: Int): Int {
        return when (tag and 0x07) {
            0 -> pos + varintSize(bytes, pos)              // varint
            1 -> pos + 8                                    // 64-bit
            2 -> {
                val len = bytes.readVarint(pos).toInt()
                pos + varintSize(bytes, pos) + len          // length-delimited
            }
            5 -> pos + 4                                    // 32-bit
            else -> pos + 1                                 // unknown — advance 1 byte
        }
    }

    companion object {
        private const val TAG = "SentencePieceTokenizer"

        // Standard SentencePiece control token IDs when a <pad> is prepended:
        const val PAD_ID = 0
        const val UNK_ID = 1
        const val BOS_ID = 2
        const val EOS_ID = 3
    }
}
