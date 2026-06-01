package com.xpenzo.ui.nav

import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavGraphBuilder
import androidx.navigation.navigation
import com.xpenzo.onboarding.OnboardingViewModel
import com.xpenzo.onboarding.ui.PhoneLoginScreen
import com.xpenzo.onboarding.ui.ProfileSetupScreen
import com.xpenzo.onboarding.ui.SmsPermissionScreen
import com.xpenzo.onboarding.ui.UpiIdSetupScreen
import com.xpenzo.onboarding.ui.VerifyOtpScreen
import com.xpenzo.onboarding.ui.WelcomeScreen
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.AutoAwesome
import androidx.compose.material.icons.rounded.Category
import androidx.compose.material.icons.rounded.Download
import androidx.compose.material.icons.rounded.Edit
import androidx.compose.material.icons.rounded.Lock
import androidx.compose.material.icons.rounded.Notifications
import androidx.compose.material.icons.rounded.Palette
import androidx.compose.material.icons.rounded.Sync
import com.xpenzo.ui.budget.BudgetScreen
import com.xpenzo.ui.categories.BrowseCategoriesScreen
import com.xpenzo.ui.common.PlaceholderScreen
import com.xpenzo.ui.home.HomeScreen
import com.xpenzo.ui.insights.InsightsScreen
import com.xpenzo.ui.settings.AiSettingsScreen
import com.xpenzo.ui.settings.AppearanceScreen
import com.xpenzo.ui.settings.AppPermissionsScreen
import com.xpenzo.ui.settings.BackupSyncScreen
import com.xpenzo.ui.settings.NotificationSettingsScreen
import com.xpenzo.ui.settings.PrivacySecurityScreen
import com.xpenzo.ui.splits.AddExpenseScreen
import com.xpenzo.ui.splits.AddFriendScreen
import com.xpenzo.ui.splits.CreateGroupScreen
import com.xpenzo.ui.splits.GroupBalancesScreen
import com.xpenzo.ui.splits.SettleUpScreen
import com.xpenzo.ui.splits.SplitsHomeScreen
import com.xpenzo.ui.settings.DeleteAccountScreen
import com.xpenzo.ui.settings.ExportDataScreen
import com.xpenzo.ui.settings.HelpImproveAiScreen
import com.xpenzo.ui.settings.SettingsScreen
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.CoralSoft
import com.xpenzo.ui.theme.Grape
import com.xpenzo.ui.theme.GrapeSoft
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.MintSoft
import com.xpenzo.ui.theme.Sky
import com.xpenzo.ui.theme.SkySoft
import com.xpenzo.ui.theme.Sun
import com.xpenzo.ui.theme.SunSoft
import com.xpenzo.ui.transactions.ManualEntryScreen
import com.xpenzo.ui.transactions.TransactionDetailScreen

/** All in-app navigation destinations. */
sealed class Screen(val route: String) {
    // Onboarding sub-graph
    data object OnboardingRoot : Screen("onboarding")
    data object Welcome        : Screen("onboarding/welcome")
    data object PhoneLogin     : Screen("onboarding/phone")
    data object VerifyOtp      : Screen("onboarding/otp")
    data object ProfileSetup   : Screen("onboarding/profile")
    data object UpiIdSetup     : Screen("onboarding/upi")
    data object SmsPermission  : Screen("onboarding/sms_permission")

    // Main app
    data object Home           : Screen("home")
    data object Budgets        : Screen("budgets")
    data object Insights       : Screen("insights")
    data object Splits         : Screen("splits")
    data object Settings       : Screen("settings")
    data object CreateGroup    : Screen("splits/create_group")
    data object AddFriend      : Screen("splits/add_friend")
    data object GroupBalances  : Screen("splits/group/{groupId}") {
        fun route(groupId: String) = "splits/group/$groupId"
    }
    data object AddExpense     : Screen("splits/group/{groupId}/add") {
        fun route(groupId: String) = "splits/group/$groupId/add"
    }
    data object SettleUp       : Screen("splits/settle?groupId={groupId}&from={from}&to={to}&amount={amount}") {
        fun route(groupId: String?, from: String, to: String, amountPaise: Long): String =
            "splits/settle?groupId=${groupId ?: ""}&from=$from&to=$to&amount=$amountPaise"
    }
    data object TransactionDetail : Screen("transaction/{id}") {
        fun route(id: String) = "transaction/$id"
    }
    data object ManualEntry    : Screen("manual_entry")
    data object SearchTx       : Screen("search")
    data object BrowseCategories : Screen("categories")
    data object AiModelSettings : Screen("ai_settings")
    data object HelpImproveAi  : Screen("ai_help")
    data object ExportData     : Screen("export")
    data object DeleteAccount  : Screen("delete_account")
    data object AppPermissions : Screen("permissions")
    data object BackupSync     : Screen("backup_sync")
    data object NotifSettings  : Screen("notif_settings")
    data object Appearance     : Screen("appearance")
    data object PrivacySecurity : Screen("privacy_security")
}

@Composable
fun XpenzoNavGraph(
    navController: NavHostController,
    startDestination: String = Screen.Home.route,
) {
    NavHost(
        navController = navController,
        startDestination = startDestination,
    ) {
        // ── Onboarding sub-graph (shares one OnboardingViewModel) ─────────────
        onboardingGraph(
            navController = navController,
            onCompleted = {
                navController.navigate(Screen.Home.route) {
                    popUpTo(Screen.OnboardingRoot.route) { inclusive = true }
                }
            },
        )

        composable(Screen.Home.route) {
            HomeScreen(
                onTransactionClick = { id ->
                    navController.navigate(Screen.TransactionDetail.route(id))
                },
                onSearchClick = { navController.navigate(Screen.SearchTx.route) },
            )
        }

        composable(Screen.Budgets.route) {
            BudgetScreen()
        }

        composable(Screen.Insights.route) {
            InsightsScreen()
        }

        composable(Screen.Settings.route) {
            SettingsScreen(navController = navController)
        }

        // ── Splits sub-graph ──────────────────────────────────────────────────
        composable(Screen.Splits.route) {
            SplitsHomeScreen(
                onCreateGroup = { navController.navigate(Screen.CreateGroup.route) },
                onAddFriend = { navController.navigate(Screen.AddFriend.route) },
                onGroupClick = { id -> navController.navigate(Screen.GroupBalances.route(id)) },
            )
        }

        composable(Screen.CreateGroup.route) {
            CreateGroupScreen(
                onBack = { navController.popBackStack() },
                onCreated = { groupId ->
                    navController.popBackStack()
                    navController.navigate(Screen.GroupBalances.route(groupId))
                },
            )
        }

        composable(Screen.AddFriend.route) {
            AddFriendScreen(
                onBack = { navController.popBackStack() },
                onSaved = { navController.popBackStack() },
            )
        }

        composable(
            route = Screen.GroupBalances.route,
            arguments = listOf(navArgument("groupId") { type = NavType.StringType }),
        ) {
            GroupBalancesScreen(
                onBack = { navController.popBackStack() },
                onAddExpense = { groupId ->
                    navController.navigate(Screen.AddExpense.route(groupId))
                },
                onSettleUp = { groupId, from, to, amount ->
                    navController.navigate(Screen.SettleUp.route(groupId, from, to, amount))
                },
            )
        }

        composable(
            route = Screen.AddExpense.route,
            arguments = listOf(navArgument("groupId") { type = NavType.StringType }),
        ) {
            AddExpenseScreen(
                onBack = { navController.popBackStack() },
                onSaved = { navController.popBackStack() },
            )
        }

        composable(
            route = Screen.SettleUp.route,
            arguments = listOf(
                navArgument("groupId") { type = NavType.StringType; nullable = true; defaultValue = null },
                navArgument("from") { type = NavType.StringType },
                navArgument("to") { type = NavType.StringType },
                navArgument("amount") { type = NavType.LongType; defaultValue = 0L },
            ),
        ) {
            SettleUpScreen(
                onBack = { navController.popBackStack() },
                onSettled = { navController.popBackStack() },
            )
        }

        composable(
            route = Screen.TransactionDetail.route,
            arguments = listOf(navArgument("id") { type = NavType.StringType }),
        ) { backStack ->
            val id = backStack.arguments?.getString("id") ?: return@composable
            TransactionDetailScreen(
                transactionId = id,
                onBack = { navController.popBackStack() },
            )
        }

        composable(Screen.SearchTx.route) {
            com.xpenzo.ui.search.SearchScreen(
                onTransactionClick = { id ->
                    navController.navigate(Screen.TransactionDetail.route(id))
                },
                onBack = { navController.popBackStack() },
            )
        }

        composable(Screen.HelpImproveAi.route) {
            HelpImproveAiScreen(onBack = { navController.popBackStack() })
        }

        composable(Screen.AppPermissions.route) {
            AppPermissionsScreen(onBack = { navController.popBackStack() })
        }

        // ── Placeholder routes (full UI coming in a follow-up iteration) ──────
        composable(Screen.ManualEntry.route) {
            ManualEntryScreen(
                onBack = { navController.popBackStack() },
                onSaved = { navController.popBackStack() },
            )
        }

        composable(Screen.BrowseCategories.route) {
            BrowseCategoriesScreen(onBack = { navController.popBackStack() })
        }

        composable(Screen.AiModelSettings.route) {
            AiSettingsScreen(onBack = { navController.popBackStack() })
        }

        composable(Screen.ExportData.route) {
            ExportDataScreen(onBack = { navController.popBackStack() })
        }

        composable(Screen.BackupSync.route) {
            BackupSyncScreen(onBack = { navController.popBackStack() })
        }

        composable(Screen.NotifSettings.route) {
            NotificationSettingsScreen(onBack = { navController.popBackStack() })
        }

        composable(Screen.Appearance.route) {
            AppearanceScreen(onBack = { navController.popBackStack() })
        }

        composable(Screen.PrivacySecurity.route) {
            PrivacySecurityScreen(
                onBack = { navController.popBackStack() },
                onExportData = { navController.navigate(Screen.ExportData.route) },
                onAppPermissions = { navController.navigate(Screen.AppPermissions.route) },
                onDeleteAccount = { navController.navigate(Screen.DeleteAccount.route) },
            )
        }

        composable(Screen.DeleteAccount.route) {
            DeleteAccountScreen(
                onAccountDeleted = {
                    // After deletion, restart the onboarding flow
                    navController.navigate(Screen.OnboardingRoot.route) {
                        popUpTo(0) { inclusive = true }
                    }
                },
                onBack = { navController.popBackStack() },
            )
        }
    }
}

/**
 * Onboarding sub-graph. All six screens share a single [OnboardingViewModel]
 * scoped to the [Screen.OnboardingRoot] nav entry so phone/OTP/profile state
 * survives navigation between screens.
 */
private fun NavGraphBuilder.onboardingGraph(
    navController: NavHostController,
    onCompleted: () -> Unit,
) {
    navigation(
        route = Screen.OnboardingRoot.route,
        startDestination = Screen.Welcome.route,
    ) {
        composable(Screen.Welcome.route) {
            WelcomeScreen(onGetStarted = { navController.navigate(Screen.PhoneLogin.route) })
        }

        composable(Screen.PhoneLogin.route) { backStack ->
            val parent = remember(backStack) {
                navController.getBackStackEntry(Screen.OnboardingRoot.route)
            }
            val vm: OnboardingViewModel = hiltViewModel(parent)
            PhoneLoginScreen(
                viewModel = vm,
                onOtpSent = { navController.navigate(Screen.VerifyOtp.route) },
                onBack = { navController.popBackStack() },
            )
        }

        composable(Screen.VerifyOtp.route) { backStack ->
            val parent = remember(backStack) {
                navController.getBackStackEntry(Screen.OnboardingRoot.route)
            }
            val vm: OnboardingViewModel = hiltViewModel(parent)
            VerifyOtpScreen(
                viewModel = vm,
                onAuthenticated = { navController.navigate(Screen.ProfileSetup.route) },
                onBack = { navController.popBackStack() },
            )
        }

        composable(Screen.ProfileSetup.route) { backStack ->
            val parent = remember(backStack) {
                navController.getBackStackEntry(Screen.OnboardingRoot.route)
            }
            val vm: OnboardingViewModel = hiltViewModel(parent)
            ProfileSetupScreen(
                viewModel = vm,
                onContinue = { navController.navigate(Screen.UpiIdSetup.route) },
            )
        }

        composable(Screen.UpiIdSetup.route) { backStack ->
            val parent = remember(backStack) {
                navController.getBackStackEntry(Screen.OnboardingRoot.route)
            }
            val vm: OnboardingViewModel = hiltViewModel(parent)
            UpiIdSetupScreen(
                viewModel = vm,
                onContinue = { navController.navigate(Screen.SmsPermission.route) },
            )
        }

        composable(Screen.SmsPermission.route) { backStack ->
            val parent = remember(backStack) {
                navController.getBackStackEntry(Screen.OnboardingRoot.route)
            }
            val vm: OnboardingViewModel = hiltViewModel(parent)
            SmsPermissionScreen(
                viewModel = vm,
                onComplete = onCompleted,
            )
        }
    }
}
