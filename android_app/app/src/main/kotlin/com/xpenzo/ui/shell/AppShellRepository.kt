package com.xpenzo.ui.shell

import com.xpenzo.ml.manager.ModelManager
import javax.inject.Inject
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine

data class AppShellState(
    val activeModel: String,
    val modelDisplayName: String,
    val modelVersion: String,
    val isReady: Boolean,
    val statusMessage: String,
    val followOnSeams: List<String>,
)

interface AppShellRepository {
    suspend fun bootstrap()
    fun state(): Flow<AppShellState>
}

class DefaultAppShellRepository @Inject constructor(
    private val modelManager: ModelManager,
) : AppShellRepository {
    override suspend fun bootstrap() {
        modelManager.initializeIfNeeded()
    }

    override fun state(): Flow<AppShellState> =
        combine(modelManager.activeModelId, modelManager.modelInfo) { activeModelId, modelInfo ->
            AppShellState(
                activeModel = activeModelId,
                modelDisplayName = modelInfo?.displayName ?: "Bootstrap pending",
                modelVersion = modelInfo?.version ?: "uninitialized",
                isReady = modelInfo != null,
                statusMessage = if (modelInfo != null) {
                    "The ML layer now resolves from android_app and the shell is ready for delivery follow-ups."
                } else {
                    "The shell is up, but model assets or runtime wiring still need follow-up."
                },
                followOnSeams = listOf(
                    "SMS ingestion: parse bank SMS into ClassifierInput before calling ModelManager.",
                    "Room persistence: replace the current habit and correction stubs with DAO-backed storage.",
                ),
            )
        }
}
