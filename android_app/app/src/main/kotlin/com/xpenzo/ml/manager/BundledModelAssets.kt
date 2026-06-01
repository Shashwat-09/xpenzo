package com.xpenzo.ml.manager

object BundledModelAssets {
    const val tfliteModel = "xpenz_cht_520.tflite"
    const val tokenizerModel = "xpenz_bpe.model"
    const val l1Labels = "labels_l1.txt"
    const val l2Labels = "labels_l2.txt"
    const val l3Labels = "labels_l3.txt"

    /** Baseline version of the bundled artifact. Remote versions must be > this to trigger a download. */
    const val version = "5.0"
}
