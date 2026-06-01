package com.xpenzo.ui.categories

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import javax.inject.Inject

/**
 * Loads the bundled `category_taxonomy.json` (sourced from
 * `ml/taxonomy/category_taxonomy.json`) and exposes the hierarchical
 * L1 → L2 → L3 tree to the UI.
 *
 * Each L3 includes example merchants and keywords, which lets users learn
 * how the model classifies their spend.
 */
@HiltViewModel
class BrowseCategoriesViewModel @Inject constructor(
    @ApplicationContext private val context: Context,
) : ViewModel() {

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    init { loadTaxonomy() }

    fun updateQuery(text: String) = _uiState.update { it.copy(query = text) }

    fun toggleL1(code: String) = _uiState.update {
        val s = it.expandedL1.toMutableSet()
        if (code in s) s.remove(code) else s.add(code)
        it.copy(expandedL1 = s)
    }

    fun toggleL2(code: String) = _uiState.update {
        val s = it.expandedL2.toMutableSet()
        if (code in s) s.remove(code) else s.add(code)
        it.copy(expandedL2 = s)
    }

    private fun loadTaxonomy() = viewModelScope.launch {
        val parsed = withContext(Dispatchers.IO) { parseTaxonomyJson() }
        _uiState.update { it.copy(taxonomy = parsed, isLoading = false) }
    }

    private fun parseTaxonomyJson(): List<L1Node> = runCatching {
        val raw = context.assets.open("category_taxonomy.json")
            .bufferedReader().use { it.readText() }
        val root = JSONObject(raw)
        val categoriesArr = root.getJSONArray("categories")

        buildList {
            for (i in 0 until categoriesArr.length()) {
                val l1 = categoriesArr.getJSONObject(i)
                val l1Code = l1.getString("l1_code")
                val l1Name = l1.getString("l1_name")
                val l1Icon = l1.optString("l1_icon", "category")

                val subArr = l1.optJSONArray("subcategories") ?: org.json.JSONArray()
                val l2List = buildList {
                    for (j in 0 until subArr.length()) {
                        val l2 = subArr.getJSONObject(j)
                        val l2Code = l2.getString("l2_code")
                        val l2Name = l2.getString("l2_name")
                        val microArr = l2.optJSONArray("micro_categories") ?: org.json.JSONArray()
                        val l3List = buildList {
                            for (k in 0 until microArr.length()) {
                                val l3 = microArr.getJSONObject(k)
                                val l3Code = l3.getString("l3_code")
                                val l3Name = l3.getString("l3_name")
                                val merchantsArr = l3.optJSONArray("example_merchants") ?: org.json.JSONArray()
                                val merchants = (0 until merchantsArr.length())
                                    .map { idx -> merchantsArr.getString(idx) }
                                add(L3Node(l3Code, l3Name, merchants))
                            }
                        }
                        add(L2Node(l2Code, l2Name, l3List))
                    }
                }
                add(L1Node(l1Code, l1Name, l1Icon, l2List))
            }
        }
    }.getOrElse { emptyList() }

    data class UiState(
        val taxonomy: List<L1Node> = emptyList(),
        val isLoading: Boolean = true,
        val query: String = "",
        val expandedL1: Set<String> = emptySet(),
        val expandedL2: Set<String> = emptySet(),
    ) {
        val filteredTaxonomy: List<L1Node> get() {
            if (query.isBlank()) return taxonomy
            return taxonomy.mapNotNull { l1 ->
                val l1Match = matches(l1.name, l1.code)
                val matchingL2 = l1.children.mapNotNull { l2 ->
                    val l2Match = matches(l2.name, l2.code)
                    val matchingL3 = l2.children.filter {
                        matches(it.name, it.code) || it.exampleMerchants.any { m -> matches(m) }
                    }
                    when {
                        matchingL3.isNotEmpty() -> l2.copy(children = matchingL3)
                        l2Match -> l2
                        else -> null
                    }
                }
                when {
                    matchingL2.isNotEmpty() -> l1.copy(children = matchingL2)
                    l1Match -> l1
                    else -> null
                }
            }
        }

        private fun matches(vararg fields: String): Boolean =
            fields.any { it.contains(query, ignoreCase = true) }
    }

    data class L1Node(val code: String, val name: String, val icon: String, val children: List<L2Node>)
    data class L2Node(val code: String, val name: String, val children: List<L3Node>)
    data class L3Node(val code: String, val name: String, val exampleMerchants: List<String>)
}
