# ─────────────────────────────────────────────────────────────────────────────
# Xpenzo — Release ProGuard rules
# Applied when buildType.release { minifyEnabled = true }
# ─────────────────────────────────────────────────────────────────────────────

# Keep our application package public APIs (avoids surprising stripping)
-keep public class com.xpenzo.XpenzoApplication { *; }
-keep public class com.xpenzo.MainActivity { *; }

# Keep Hilt-generated components (required for DI to work at runtime)
-keep,allowobfuscation @interface dagger.**
-keep,allowobfuscation @interface javax.inject.**
-keep class * extends dagger.hilt.android.internal.lifecycle.HiltViewModelFactory { *; }
-keep class hilt_aggregated_deps.** { *; }
-keep class * extends dagger.hilt.android.internal.managers.ApplicationComponentManager { *; }
-keep class **_HiltModules { *; }
-keepclasseswithmembers class * {
    @dagger.hilt.android.lifecycle.HiltViewModel <init>(...);
}
-keep class * extends androidx.hilt.work.HiltWorkerFactory

# Workers — preserve constructors for WorkManager reflection
-keep class * extends androidx.work.ListenableWorker {
    public <init>(android.content.Context, androidx.work.WorkerParameters);
}

# Room (entities and DAOs are referenced via generated code)
-keep class com.xpenzo.data.db.entity.** { *; }
-keep class com.xpenzo.data.db.dao.** { *; }
-keep class com.xpenzo.data.db.XpenzoDatabase { *; }
-keepattributes *Annotation*
-dontwarn androidx.room.paging.**

# Kotlin coroutines internals
-keepnames class kotlinx.coroutines.internal.MainDispatcherFactory {}
-keepnames class kotlinx.coroutines.CoroutineExceptionHandler {}

# TensorFlow Lite — native bindings + generated code
-keep class org.tensorflow.lite.** { *; }
-keep class org.tensorflow.lite.support.** { *; }
-keep class org.tensorflow.lite.gpu.** { *; }
-dontwarn org.tensorflow.lite.**

# Firebase — Crashlytics requires line numbers + file names
-keepattributes SourceFile,LineNumberTable
-keep class com.google.firebase.** { *; }
-keep class com.google.android.gms.** { *; }
-dontwarn com.google.firebase.**
-dontwarn com.google.android.gms.**

# Jetpack Compose runtime
-dontwarn androidx.compose.**
-keep class androidx.compose.runtime.** { *; }

# Navigation Compose — preserve composable destinations
-keep class androidx.navigation.compose.** { *; }

# JSON serialization (Firestore uses internal reflection on data classes)
-keepclassmembers class com.xpenzo.** {
    public <init>(...);
    public static *;
}
-keepclasseswithmembers class com.xpenzo.firebase.** { *; }

# Kotlin metadata is needed for reflection-based libraries
-keep class kotlin.Metadata { *; }
-keep class kotlin.reflect.** { *; }

# Keep generic signatures for Gson/Moshi/Firestore reflection
-keepattributes Signature
-keepattributes Exceptions
-keepattributes RuntimeVisibleAnnotations
-keepattributes RuntimeVisibleParameterAnnotations
-keepattributes EnclosingMethod
-keepattributes InnerClasses

# Don't warn about missing classes from upstream artifacts we don't use
-dontwarn javax.annotation.**
-dontwarn org.checkerframework.**
-dontwarn org.codehaus.mojo.animal_sniffer.**
