package com.xpenzo.ui.splits

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ArrowBack
import androidx.compose.material.icons.rounded.PersonAdd
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xpenzo.splits.SplitsRepository
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Sun
import com.xpenzo.ui.theme.SunSoft
import com.xpenzo.ui.theme.Surface
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AddFriendViewModel @Inject constructor(
    private val splitsRepository: SplitsRepository,
) : ViewModel() {
    suspend fun add(name: String, phone: String?): Boolean {
        if (name.isBlank()) return false
        splitsRepository.addFriend(
            displayName = name.trim(),
            phoneE164 = phone?.takeIf { it.isNotBlank() }?.let {
                if (it.startsWith("+")) it else "+91${it.filter { c -> c.isDigit() }}"
            },
            otherUserId = null, // ghost friend until they sign up
        )
        return true
    }
}

@Composable
fun AddFriendScreen(
    onBack: () -> Unit,
    onSaved: () -> Unit,
    viewModel: AddFriendViewModel = hiltViewModel(),
) {
    var name by remember { mutableStateOf("") }
    var phone by remember { mutableStateOf("") }
    var saving by remember { mutableStateOf(false) }
    val scope = androidx.compose.runtime.rememberCoroutineScope()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Cream),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(start = 8.dp, top = 16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onBack) {
                Icon(Icons.Rounded.ArrowBack, contentDescription = "Back", tint = Ink)
            }
            Text(
                "Add friend",
                style = MaterialTheme.typography.titleLarge.copy(
                    fontWeight = FontWeight.Bold, color = Ink,
                ),
            )
        }

        Column(
            modifier = Modifier.padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Box(
                modifier = Modifier
                    .size(80.dp)
                    .background(SunSoft, RoundedCornerShape(24.dp))
                    .align(Alignment.CenterHorizontally),
                contentAlignment = Alignment.Center,
            ) {
                Icon(Icons.Rounded.PersonAdd, contentDescription = null, tint = Sun, modifier = Modifier.size(40.dp))
            }

            OutlinedTextField(
                value = name,
                onValueChange = { name = it.take(50) },
                label = { Text("Friend's name") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = Sun, cursorColor = Sun,
                    focusedContainerColor = Surface, unfocusedContainerColor = Surface,
                ),
            )

            OutlinedTextField(
                value = phone,
                onValueChange = { phone = it.filter { c -> c.isDigit() }.take(10) },
                label = { Text("Phone (optional)") },
                placeholder = { Text("98765 43210") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
                leadingIcon = {
                    Text("+91", modifier = Modifier.padding(start = 12.dp), color = Ink,
                        style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.SemiBold))
                },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = Sun, cursorColor = Sun,
                    focusedContainerColor = Surface, unfocusedContainerColor = Surface,
                ),
            )

            Text(
                "If your friend isn't on Xpenzo yet, we'll track them as a 'ghost' friend " +
                    "and link them automatically once they sign up.",
                style = MaterialTheme.typography.bodySmall, color = Muted,
            )

            Spacer(Modifier.weight(1f))

            Button(
                onClick = {
                    if (name.isBlank() || saving) return@Button
                    saving = true
                    scope.launch {
                        viewModel.add(name, phone.takeIf { it.isNotBlank() })
                        saving = false
                        onSaved()
                    }
                },
                enabled = name.isNotBlank() && !saving,
                modifier = Modifier.fillMaxWidth().height(56.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Coral),
                shape = RoundedCornerShape(20.dp),
            ) {
                Text(if (saving) "Saving…" else "Add friend",
                    fontWeight = FontWeight.SemiBold, color = Surface)
            }
        }
    }
}
