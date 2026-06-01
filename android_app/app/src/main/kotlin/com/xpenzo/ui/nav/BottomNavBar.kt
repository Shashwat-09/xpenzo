package com.xpenzo.ui.nav

import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Groups
import androidx.compose.material.icons.rounded.Home
import androidx.compose.material.icons.rounded.PieChart
import androidx.compose.material.icons.rounded.Settings
import androidx.compose.material.icons.rounded.ShowChart
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import androidx.navigation.compose.currentBackStackEntryAsState
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Muted

private data class BottomNavItem(
    val label: String,
    val icon: ImageVector,
    val route: String,
)

private val NAV_ITEMS = listOf(
    BottomNavItem("Home",     Icons.Rounded.Home,      Screen.Home.route),
    BottomNavItem("Budgets",  Icons.Rounded.PieChart,  Screen.Budgets.route),
    BottomNavItem("Splits",   Icons.Rounded.Groups,    Screen.Splits.route),
    BottomNavItem("Insights", Icons.Rounded.ShowChart, Screen.Insights.route),
    BottomNavItem("Settings", Icons.Rounded.Settings,  Screen.Settings.route),
)

@Composable
fun BottomNavBar(navController: NavController) {
    val backStack by navController.currentBackStackEntryAsState()
    val currentRoute = backStack?.destination?.route

    NavigationBar(
        containerColor = Cream,
        tonalElevation = 0.dp,
    ) {
        NAV_ITEMS.forEach { item ->
            val selected = currentRoute == item.route
            NavigationBarItem(
                selected = selected,
                onClick = {
                    if (!selected) {
                        navController.navigate(item.route) {
                            popUpTo(Screen.Home.route) { saveState = true }
                            launchSingleTop = true
                            restoreState = true
                        }
                    }
                },
                icon = {
                    Icon(
                        imageVector = item.icon,
                        contentDescription = item.label,
                        modifier = Modifier.size(24.dp),
                    )
                },
                label = {
                    Text(
                        text = item.label,
                        style = MaterialTheme.typography.labelMedium,
                    )
                },
                colors = NavigationBarItemDefaults.colors(
                    selectedIconColor = Coral,
                    selectedTextColor = Coral,
                    unselectedIconColor = Muted,
                    unselectedTextColor = Muted,
                    indicatorColor = Coral.copy(alpha = 0.12f),
                ),
            )
        }
    }
}
