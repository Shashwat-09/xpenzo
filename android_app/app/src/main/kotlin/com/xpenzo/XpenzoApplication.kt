package com.xpenzo

import android.app.Application
import android.util.Log
import androidx.hilt.work.HiltWorkerFactory
import androidx.work.Configuration
import com.google.firebase.FirebaseApp
import com.google.firebase.crashlytics.FirebaseCrashlytics
import com.xpenzo.firebase.ModelUpdateManager
import com.xpenzo.firebase.SyncWorker
import dagger.hilt.android.HiltAndroidApp
import javax.inject.Inject

@HiltAndroidApp
class XpenzoApplication : Application(), Configuration.Provider {

    @Inject
    lateinit var workerFactory: HiltWorkerFactory

    @Inject
    lateinit var modelUpdateManager: ModelUpdateManager

    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setWorkerFactory(workerFactory)
            .build()

    override fun onCreate() {
        super.onCreate()

        // Daily Wi-Fi-only model update check (no-op until Firebase is configured)
        modelUpdateManager.schedulePeriodicChecks()
        // 6-hour Firestore sync (transactions + corrections)
        SyncWorker.schedule(this)

        // Firebase-dependent init — guarded so the app boots even when
        // google-services.json is missing (e.g. early-stage dev builds).
        if (FirebaseApp.getApps(this).isNotEmpty()) {
            runCatching {
                FirebaseCrashlytics.getInstance()
                    .setCrashlyticsCollectionEnabled(!BuildConfig.DEBUG)
            }.onFailure { Log.w(TAG, "Crashlytics init failed", it) }
        } else {
            Log.w(TAG, "Firebase not configured — Crashlytics + Auth + Firestore disabled. " +
                "Drop google-services.json in app/ to enable.")
        }
    }

    private companion object {
        const val TAG = "XpenzoApplication"
    }
}
