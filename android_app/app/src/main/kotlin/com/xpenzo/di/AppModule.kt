package com.xpenzo.di

import android.content.Context
import com.xpenzo.data.repository.TransactionRepository
import com.xpenzo.ml.manager.ModelManager
import com.xpenzo.ml.models.RoomBackedHabitModel
import com.xpenzo.ui.shell.AppShellRepository
import com.xpenzo.ui.shell.DefaultAppShellRepository
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideRoomBackedHabitModel(repository: TransactionRepository): RoomBackedHabitModel =
        RoomBackedHabitModel(repository)

    @Provides
    @Singleton
    fun provideModelManager(
        @ApplicationContext context: Context,
        habitModel: RoomBackedHabitModel,
    ): ModelManager = ModelManager.getInstance(context, habitModel)

    @Provides
    @Singleton
    fun provideAppShellRepository(modelManager: ModelManager): AppShellRepository =
        DefaultAppShellRepository(modelManager)
}
