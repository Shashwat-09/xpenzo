package com.xpenzo.di

import android.content.Context
import com.xpenzo.data.repository.TransactionRepository
import com.xpenzo.firebase.AuthRepository
import com.xpenzo.firebase.FirestoreSyncRepository
import com.xpenzo.firebase.ModelUpdateManager
import com.xpenzo.ml.data.DataCollectionManager
import com.xpenzo.ml.manager.ModelManager
import com.xpenzo.ml.models.RoomBackedHabitModel
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object FirebaseModule {

    @Provides
    @Singleton
    fun provideAuthRepository(): AuthRepository = AuthRepository()

    @Provides
    @Singleton
    fun provideModelUpdateManager(
        @ApplicationContext context: Context,
        modelManager: ModelManager,
    ): ModelUpdateManager = ModelUpdateManager(context, modelManager)

    @Provides
    @Singleton
    fun provideFirestoreSyncRepository(
        repository: TransactionRepository,
        auth: AuthRepository,
    ): FirestoreSyncRepository = FirestoreSyncRepository(repository, auth)

    @Provides
    @Singleton
    fun provideDataCollectionManager(
        @ApplicationContext context: Context,
        habitModel: RoomBackedHabitModel,
        repository: TransactionRepository,
    ): DataCollectionManager = DataCollectionManager(context, habitModel, repository)
}
