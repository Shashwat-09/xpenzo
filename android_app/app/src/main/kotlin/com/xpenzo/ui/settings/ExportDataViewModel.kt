package com.xpenzo.ui.settings

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.core.content.FileProvider
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xpenzo.data.db.entity.TransactionEntity
import com.xpenzo.data.repository.TransactionRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileWriter
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import javax.inject.Inject

/**
 * Generates a CSV export of every transaction in the Room database and offers
 * it via the system share sheet. Implements the user's DPDP Act 2023 right to
 * data portability.
 */
@HiltViewModel
class ExportDataViewModel @Inject constructor(
    @ApplicationContext private val context: Context,
    private val repository: TransactionRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    /** Generate the CSV and emit a [UiState] containing a content URI to share. */
    fun exportCsv() = viewModelScope.launch {
        _uiState.update { it.copy(isExporting = true, error = null, fileUri = null) }
        runCatching {
            val transactions = withContext(Dispatchers.IO) { repository.getAllTransactionsOnce() }
            val file = withContext(Dispatchers.IO) { writeCsv(transactions) }
            val uri = FileProvider.getUriForFile(
                context, "${context.packageName}.fileprovider", file,
            )
            _uiState.update {
                it.copy(
                    isExporting = false,
                    fileUri = uri,
                    transactionCount = transactions.size,
                )
            }
        }.onFailure { e ->
            _uiState.update { it.copy(isExporting = false, error = e.message ?: "Export failed") }
        }
    }

    /** Build an Android share intent for the generated CSV. */
    fun buildShareIntent(uri: Uri): Intent = Intent(Intent.ACTION_SEND).apply {
        type = "text/csv"
        putExtra(Intent.EXTRA_STREAM, uri)
        putExtra(Intent.EXTRA_SUBJECT, "Xpenzo transactions export")
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }

    // ── CSV writer ───────────────────────────────────────────────────────────

    private fun writeCsv(transactions: List<TransactionEntity>): File {
        val dir = File(context.cacheDir, "exports").apply { mkdirs() }
        val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
        val file = File(dir, "xpenzo_transactions_$timestamp.csv")

        FileWriter(file).use { w ->
            w.appendLine(CSV_HEADER)
            transactions.forEach { tx ->
                w.appendLine(tx.toCsvRow())
            }
        }
        return file
    }

    private fun TransactionEntity.toCsvRow(): String = listOf(
        id,
        merchantRaw.escapeCsv(),
        merchantNormalized.escapeCsv(),
        upiId.escapeCsv(),
        "%.2f".format(amount / 100.0),
        if (isCredit) "credit" else "debit",
        DATE_FORMAT.format(Date(timestamp)),
        l1Category.escapeCsv(),
        l2Category.escapeCsv(),
        l3Category.escapeCsv(),
        "%.3f".format(confidence),
        source,
        if (isCorrected) "1" else "0",
        if (synced) "1" else "0",
    ).joinToString(",")

    private fun String.escapeCsv(): String =
        if (any { it in CSV_SPECIAL_CHARS }) {
            "\"" + replace("\"", "\"\"") + "\""
        } else this

    // ── UI model ─────────────────────────────────────────────────────────────

    data class UiState(
        val isExporting: Boolean = false,
        val fileUri: Uri? = null,
        val transactionCount: Int = 0,
        val error: String? = null,
    )

    private companion object {
        const val CSV_HEADER = "id,merchant_raw,merchant_normalized,upi_id,amount_rupees," +
            "direction,timestamp,l1_category,l2_category,l3_category," +
            "confidence,source,is_corrected,synced"
        val DATE_FORMAT: SimpleDateFormat =
            SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.US)
        val CSV_SPECIAL_CHARS = setOf(',', '"', '\n', '\r')
    }
}
