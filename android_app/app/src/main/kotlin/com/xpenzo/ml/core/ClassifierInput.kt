package com.xpenzo.ml.core

import java.time.LocalDateTime

data class ClassifierInput(
    val merchantName: String,
    val upiId: String,
    val amount: Double,
    val timestamp: LocalDateTime = LocalDateTime.now(),
    val latitude: Double? = null,
    val longitude: Double? = null,
    val rawSms: String = "",
)
