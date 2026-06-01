package com.xpenzo.ml.core

interface TransactionClassifier {
    suspend fun classify(input: ClassifierInput): ClassificationResult
    suspend fun warmUp()
    fun close()

    val displayName: String
    val version: String
    val modelSizeBytes: Long
    val supportsColdStart: Boolean
}
