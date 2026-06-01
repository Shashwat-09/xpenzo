package com.xpenzo.di

import android.content.Context
import androidx.room.Room
import com.xpenzo.data.db.XpenzoDatabase
import com.xpenzo.data.db.dao.BudgetDao
import com.xpenzo.data.db.dao.CorrectionDao
import com.xpenzo.data.db.dao.FriendDao
import com.xpenzo.data.db.dao.GroupDao
import com.xpenzo.data.db.dao.HabitDao
import com.xpenzo.data.db.dao.SplitDao
import com.xpenzo.data.db.dao.TransactionDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): XpenzoDatabase =
        Room.databaseBuilder(
            context,
            XpenzoDatabase::class.java,
            XpenzoDatabase.DATABASE_NAME,
        )
            .addMigrations(XpenzoDatabase.MIGRATION_1_2)
            // Fallback only if user is on a pre-release dev build with an unknown schema —
            // explicit migration above is always preferred for production users.
            .fallbackToDestructiveMigrationFrom(/* legacyVersions = */ 0)
            .build()

    @Provides
    fun provideTransactionDao(db: XpenzoDatabase): TransactionDao = db.transactionDao()

    @Provides
    fun provideHabitDao(db: XpenzoDatabase): HabitDao = db.habitDao()

    @Provides
    fun provideCorrectionDao(db: XpenzoDatabase): CorrectionDao = db.correctionDao()

    @Provides
    fun provideBudgetDao(db: XpenzoDatabase): BudgetDao = db.budgetDao()

    @Provides
    fun provideGroupDao(db: XpenzoDatabase): GroupDao = db.groupDao()

    @Provides
    fun provideSplitDao(db: XpenzoDatabase): SplitDao = db.splitDao()

    @Provides
    fun provideFriendDao(db: XpenzoDatabase): FriendDao = db.friendDao()
}
