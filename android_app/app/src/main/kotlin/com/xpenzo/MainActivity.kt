package com.xpenzo

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.xpenzo.onboarding.OnboardingPreferences
import com.xpenzo.ui.nav.BottomNavBar
import com.xpenzo.ui.nav.Screen
import com.xpenzo.ui.nav.XpenzoNavGraph
import com.xpenzo.ui.theme.XpenzoTheme
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

/**
 * Routes the user to onboarding on first launch (or after account deletion),
 * to the main app once onboarding is complete.
 *
 * The bottom nav bar is hidden during onboarding and on detail screens.
 */
private val BOTTOM_NAV_ROUTES = setOf(
    Screen.Home.route,
    Screen.Budgets.route,
    Screen.Splits.route,
    Screen.Insights.route,
    Screen.Settings.route,
)

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @Inject
    lateinit var onboardingPreferences: OnboardingPreferences

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val startDestination = if (onboardingPreferences.isCompleted) {
            Screen.Home.route
        } else {
            Screen.OnboardingRoot.route
        }

        setContent {
            XpenzoTheme {
                val navController = rememberNavController()
                val currentEntry by navController.currentBackStackEntryAsState()
                val currentRoute = currentEntry?.destination?.route

                Scaffold(
                    modifier = Modifier.fillMaxSize(),
                    bottomBar = {
                        if (currentRoute in BOTTOM_NAV_ROUTES) {
                            BottomNavBar(navController = navController)
                        }
                    },
                ) { _ ->
                    XpenzoNavGraph(
                        navController = navController,
                        startDestination = startDestination,
                    )
                }
            }
        }
    }
}
