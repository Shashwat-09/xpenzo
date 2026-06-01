package com.xpenzo.ui.splits

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Add
import androidx.compose.material.icons.rounded.GroupAdd
import androidx.compose.material.icons.rounded.Groups
import androidx.compose.material.icons.rounded.Person
import androidx.compose.material.icons.rounded.PersonAdd
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.xpenzo.data.db.entity.FriendEntity
import com.xpenzo.data.db.entity.GroupEntity
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.CoralSoft
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Grape
import com.xpenzo.ui.theme.GrapeSoft
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.MintSoft
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Sun
import com.xpenzo.ui.theme.SunSoft
import com.xpenzo.ui.theme.Surface

@OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)
@Composable
fun SplitsHomeScreen(
    onCreateGroup: () -> Unit,
    onAddFriend: () -> Unit,
    onGroupClick: (String) -> Unit,
    viewModel: SplitsHomeViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    var showAddSheet by remember { mutableStateOf(false) }

    Scaffold(
        containerColor = Cream,
        floatingActionButton = {
            FloatingActionButton(
                onClick = { showAddSheet = true },
                containerColor = Coral,
                contentColor = Surface,
                shape = CircleShape,
            ) { Icon(Icons.Rounded.Add, contentDescription = "Add") }
        },
    ) { inner ->
        Column(modifier = Modifier.padding(inner).fillMaxSize()) {
            Text(
                "Splits",
                style = MaterialTheme.typography.headlineLarge.copy(
                    fontWeight = FontWeight.Bold, color = Ink,
                ),
                modifier = Modifier.padding(start = 24.dp, top = 24.dp, bottom = 16.dp),
            )

            if (state.isLoading) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
                return@Column
            }

            if (!state.hasContent) {
                EmptyState(onCreateGroup = onCreateGroup, onAddFriend = onAddFriend)
                return@Column
            }

            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                if (state.groups.isNotEmpty()) {
                    item {
                        SectionHeader("Groups", Icons.Rounded.Groups, Grape, GrapeSoft)
                    }
                    items(state.groups, key = { it.id }) { group ->
                        GroupCard(group = group, onClick = { onGroupClick(group.id) })
                    }
                }

                if (state.friends.isNotEmpty()) {
                    item {
                        SectionHeader("Friends", Icons.Rounded.Person, Sun, SunSoft)
                    }
                    items(state.friends, key = { it.id }) { friend ->
                        FriendCard(friend)
                    }
                }
            }
        }
    }

    if (showAddSheet) {
        ModalBottomSheet(onDismissRequest = { showAddSheet = false }) {
            Column(Modifier.padding(24.dp)) {
                Text("Add new",
                    style = MaterialTheme.typography.titleLarge.copy(
                        fontWeight = FontWeight.Bold, color = Ink,
                    ),
                )
                Spacer(Modifier.height(16.dp))

                AddRow(
                    icon = Icons.Rounded.GroupAdd,
                    iconBg = GrapeSoft, iconTint = Grape,
                    title = "Create group",
                    subtitle = "Trip, flatmates, couple — split with multiple people",
                    onClick = { showAddSheet = false; onCreateGroup() },
                )

                Spacer(Modifier.height(8.dp))

                AddRow(
                    icon = Icons.Rounded.PersonAdd,
                    iconBg = SunSoft, iconTint = Sun,
                    title = "Add friend",
                    subtitle = "1:1 splits — no group container needed",
                    onClick = { showAddSheet = false; onAddFriend() },
                )

                Spacer(Modifier.height(16.dp))
            }
        }
    }
}

@Composable
private fun EmptyState(onCreateGroup: () -> Unit, onAddFriend: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxSize().padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Box(
            modifier = Modifier
                .size(96.dp)
                .background(CoralSoft, RoundedCornerShape(28.dp)),
            contentAlignment = Alignment.Center,
        ) {
            Icon(Icons.Rounded.Groups, contentDescription = null, tint = Coral, modifier = Modifier.size(48.dp))
        }
        Spacer(Modifier.height(24.dp))
        Text(
            "Split bills with friends",
            style = MaterialTheme.typography.headlineSmall.copy(
                fontWeight = FontWeight.Bold, color = Ink,
            ),
        )
        Spacer(Modifier.height(8.dp))
        Text(
            "Track shared expenses with flatmates, on trips, " +
                "or anywhere money flows between people.",
            style = MaterialTheme.typography.bodyMedium,
            color = Muted,
            textAlign = TextAlign.Center,
        )
        Spacer(Modifier.height(32.dp))

        Button(
            onClick = onCreateGroup,
            modifier = Modifier.fillMaxWidth().height(56.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Grape),
            shape = RoundedCornerShape(16.dp),
        ) {
            Icon(Icons.Rounded.GroupAdd, contentDescription = null, tint = Surface)
            Spacer(Modifier.width(8.dp))
            Text("Create your first group", fontWeight = FontWeight.SemiBold, color = Surface)
        }
        Spacer(Modifier.height(8.dp))
        OutlinedButton(
            onClick = onAddFriend,
            modifier = Modifier.fillMaxWidth().height(56.dp),
            shape = RoundedCornerShape(16.dp),
        ) {
            Icon(Icons.Rounded.PersonAdd, contentDescription = null)
            Spacer(Modifier.width(8.dp))
            Text("Add a friend instead")
        }
    }
}

@Composable
private fun SectionHeader(
    title: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    color: androidx.compose.ui.graphics.Color,
    bg: androidx.compose.ui.graphics.Color,
) {
    Row(
        modifier = Modifier.padding(vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            modifier = Modifier
                .size(28.dp)
                .background(bg, RoundedCornerShape(8.dp)),
            contentAlignment = Alignment.Center,
        ) {
            Icon(icon, contentDescription = null, tint = color, modifier = Modifier.size(16.dp))
        }
        Spacer(Modifier.width(8.dp))
        Text(
            title.uppercase(),
            style = MaterialTheme.typography.labelMedium.copy(
                fontWeight = FontWeight.Bold, color = Muted,
            ),
        )
    }
}

@Composable
private fun GroupCard(group: GroupEntity, onClick: () -> Unit) {
    Card(
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Surface),
        elevation = CardDefaults.cardElevation(1.dp),
        onClick = onClick,
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .clip(RoundedCornerShape(14.dp))
                    .background(Grape.copy(alpha = 0.15f)),
                contentAlignment = Alignment.Center,
            ) {
                Text(group.emoji, style = MaterialTheme.typography.titleLarge)
            }
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(
                    group.name,
                    style = MaterialTheme.typography.titleMedium.copy(
                        fontWeight = FontWeight.SemiBold, color = Ink,
                    ),
                )
                Text("Tap to view balances", style = MaterialTheme.typography.bodySmall, color = Muted)
            }
        }
    }
}

@Composable
private fun FriendCard(friend: FriendEntity) {
    Card(
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Surface),
        elevation = CardDefaults.cardElevation(1.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .background(Sun.copy(alpha = 0.18f), CircleShape),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    friend.displayName.take(1).uppercase(),
                    style = MaterialTheme.typography.titleMedium.copy(
                        fontWeight = FontWeight.Bold, color = Sun,
                    ),
                )
            }
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(
                    friend.displayName,
                    style = MaterialTheme.typography.titleMedium.copy(
                        fontWeight = FontWeight.SemiBold, color = Ink,
                    ),
                )
                Text(
                    friend.phoneE164 ?: if (friend.isGhost) "Not on Xpenzo yet" else "On Xpenzo",
                    style = MaterialTheme.typography.bodySmall,
                    color = Muted,
                )
            }
        }
    }
}

@Composable
private fun AddRow(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    iconBg: androidx.compose.ui.graphics.Color,
    iconTint: androidx.compose.ui.graphics.Color,
    title: String,
    subtitle: String,
    onClick: () -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .clickable(onClick = onClick)
            .padding(12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            modifier = Modifier.size(44.dp).background(iconBg, RoundedCornerShape(12.dp)),
            contentAlignment = Alignment.Center,
        ) { Icon(icon, contentDescription = null, tint = iconTint, modifier = Modifier.size(22.dp)) }
        Spacer(Modifier.width(14.dp))
        Column(Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.titleMedium.copy(
                fontWeight = FontWeight.SemiBold, color = Ink,
            ))
            Text(subtitle, style = MaterialTheme.typography.bodySmall, color = Muted)
        }
    }
}
