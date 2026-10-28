<template>
  <v-app :theme="theme">
    <!-- Top Navigation Bar -->
    <v-app-bar flat border density="comfortable" color="surface">
      <v-app-bar-title class="d-flex align-center font-weight-bold">
        <v-icon icon="mdi-robot-outline" color="primary" class="mr-2"></v-icon>
        AiAgents Benchmark
        <span class="text-caption text-medium-emphasis ml-2 d-none d-sm-inline">
          Praca Inżynierska • Solo vs Multi-Agent Swarm
        </span>
      </v-app-bar-title>

      <v-spacer></v-spacer>

      <!-- Hardware & Ollama Status Chips -->
      <v-chip
        size="small"
        :color="status.ollama_online ? 'success' : 'error'"
        variant="tonal"
        class="mr-2"
        prepend-icon="mdi-server"
      >
        Ollama: {{ status.ollama_online ? 'Połączono' : 'Offline' }}
      </v-chip>

      <v-chip
        size="small"
        color="accent"
        variant="tonal"
        class="mr-2 d-none d-md-flex"
        prepend-icon="mdi-expansion-card"
        :title="status.gpu_telemetry ? `VRAM: ${status.gpu_telemetry.used_vram_mb}/${status.gpu_telemetry.total_vram_mb} MB | Temp: ${status.gpu_telemetry.temperature_c}°C` : ''"
      >
        RTX 5080: {{ status.gpu_telemetry?.used_vram_mb || 1397 }} MB ({{ status.gpu_telemetry?.temperature_c || 33 }}°C)
      </v-chip>

      <!-- Ollama Models Dialog Button -->
      <v-btn
        size="small"
        variant="tonal"
        color="primary"
        prepend-icon="mdi-download"
        class="mr-2"
        @click="openModelDialog"
      >
        Modele Ollama
      </v-btn>

      <!-- Provider Select -->
      <div style="width: 140px;" class="mr-2">
        <v-select
          v-model="selectedProvider"
          :items="providers"
          density="compact"
          variant="outlined"
          hide-details
          label="Dostawca"
        ></v-select>
      </div>

      <!-- Theme Switch -->
      <v-btn
        icon
        variant="text"
        size="small"
        @click="toggleTheme"
        :title="theme === 'dark' ? 'Tryb jasny' : 'Tryb ciemny'"
      >
        <v-icon>{{ theme === 'dark' ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
      </v-btn>
    </v-app-bar>

    <!-- Main Content with Tabs -->
    <v-main>
      <v-container fluid class="pa-4 pa-md-6">
        <!-- Navigation Tabs -->
        <v-tabs v-model="activeTab" color="primary" class="mb-4" align-tabs="start">
          <v-tab value="dashboard" prepend-icon="mdi-view-dashboard-outline">
            Centrum Sterowania
          </v-tab>
          <v-tab value="lab" prepend-icon="mdi-flask-outline">
            Laboratorium Zadania & Debata
          </v-tab>
          <v-tab value="agents" prepend-icon="mdi-account-group-outline">
            Konfiguracja Agentów i Modeli
          </v-tab>
          <v-tab value="results" prepend-icon="mdi-chart-line">
            Wyniki & Wykresy (300 DPI)
          </v-tab>
          <v-tab value="thesis" prepend-icon="mdi-book-open-page-variant-outline">
            Rozdział Pracy Inżynierskiej (LaTeX)
          </v-tab>
        </v-tabs>

        <v-window v-model="activeTab">
          <!-- TAB 1: CENTRUM STEROWANIA -->
          <v-window-item value="dashboard">
            <!-- KPI Summary Cards -->
            <v-row class="mb-2">
              <v-col cols="12" sm="6" md="3">
                <v-card border elevation="0" class="pa-4 rounded-lg">
                  <div class="text-caption text-medium-emphasis">Postęp Zadań</div>
                  <div class="text-h5 font-weight-bold mt-1 text-primary">
                    {{ status.completed_count }} / {{ status.total_count }}
                  </div>
                  <v-progress-linear
                    :model-value="(status.completed_count / status.total_count) * 100"
                    color="primary"
                    height="6"
                    rounded
                    class="mt-2"
                  ></v-progress-linear>
                </v-card>
              </v-col>

              <v-col cols="12" sm="6" md="3">
                <v-card border elevation="0" class="pa-4 rounded-lg">
                  <div class="text-caption text-medium-emphasis">Średni Wynik Solo vs Swarm</div>
                  <div class="text-h5 font-weight-bold mt-1">
                    <span class="text-medium-emphasis">{{ stats.solo_mean || 0 }}</span>
                    <span class="mx-2 text-disabled">vs</span>
                    <span class="text-secondary">{{ stats.multi_mean || 0 }} pkt</span>
                  </div>
                  <div class="text-caption mt-1" :class="(stats.score_delta || 0) >= 0 ? 'text-secondary' : 'text-error'">
                    Przewaga Roje: {{ (stats.score_delta || 0) > 0 ? '+' : '' }}{{ stats.score_delta || 0 }} pkt
                  </div>
                </v-card>
              </v-col>

              <v-col cols="12" sm="6" md="3">
                <v-card border elevation="0" class="pa-4 rounded-lg">
                  <div class="text-caption text-medium-emphasis">Istotność Statystyczna (Wilcoxon)</div>
                  <div class="text-h5 font-weight-bold mt-1 text-accent d-flex align-center">
                    p {{ stats.wilcoxon_pvalue != null ? (stats.wilcoxon_pvalue < 0.001 ? '< 0.001' : '= ' + stats.wilcoxon_pvalue) : 'N/A' }}
                    <v-chip v-if="stats.wilcoxon_pvalue != null && stats.wilcoxon_pvalue < 0.05" size="x-small" color="success" class="ml-2 font-weight-bold">p &lt; 0.05</v-chip>
                  </div>
                  <div class="text-caption text-medium-emphasis mt-1">
                    Wielkość efektu: d = {{ stats.cohens_d != null ? stats.cohens_d : 'N/A' }} {{ (stats.cohens_d || 0) >= 0.8 ? '(duży efekt)' : '' }}
                  </div>
                </v-card>
              </v-col>

              <v-col cols="12" sm="6" md="3">
                <v-card border elevation="0" class="pa-4 rounded-lg">
                  <div class="text-caption text-medium-emphasis">Status Silnika Badawczego</div>
                  <div class="text-h5 font-weight-bold mt-1 d-flex align-center">
                    <v-badge
                      inline
                      dot
                      :color="status.benchmark_running ? 'warning' : 'success'"
                      class="mr-2"
                    ></v-badge>
                    {{ status.benchmark_running ? 'W Toku' : 'Gotowy' }}
                  </div>
                  <div class="text-caption text-truncate text-medium-emphasis mt-1">
                    {{ status.current_step || 'Oczekiwanie na dyspozycję' }}
                  </div>
                </v-card>
              </v-col>
            </v-row>

            <!-- Control Box & Execution Trigger -->
            <v-row>
              <v-col cols="12" md="8">
                <v-card border elevation="0" class="pa-5 rounded-lg mb-4">
                  <div class="d-flex align-center mb-4">
                    <v-icon icon="mdi-play-circle-outline" color="primary" class="mr-2" size="28"></v-icon>
                    <div>
                      <div class="text-h6 font-weight-bold">Sterowanie Badaniem Masowym</div>
                      <div class="text-caption text-medium-emphasis">
                        Uruchom porównanie modeli dla całego korpusu lub wybranej kategorii
                      </div>
                    </div>
                  </div>

                  <v-row dense>
                    <v-col cols="12" sm="6">
                      <v-select
                        v-model="filterCategory"
                        :items="['Wszystkie kategorie', ...categories]"
                        label="Kategoria zadań"
                        variant="outlined"
                        density="comfortable"
                      ></v-select>
                    </v-col>
                    <v-col cols="12" sm="6">
                      <v-select
                        v-model="filterDifficulty"
                        :items="['Wszystkie trudności', 'easy', 'medium', 'hard']"
                        label="Poziom trudności"
                        variant="outlined"
                        density="comfortable"
                      ></v-select>
                    </v-col>
                    <v-col cols="12" sm="6">
                      <v-switch
                        v-model="resumeCheckpoint"
                        color="primary"
                        label="Wznawiaj od checkpointu (pomiń ukończone)"
                        hide-details
                        density="compact"
                      ></v-switch>
                    </v-col>
                    <v-col cols="12" sm="6">
                      <v-switch
                        v-model="dryRun"
                        color="warning"
                        label="Tryb testowy potoku (Dry Run Mock)"
                        hide-details
                        density="compact"
                      ></v-switch>
                    </v-col>
                  </v-row>

                  <v-divider class="my-4"></v-divider>

                  <div class="d-flex gap-3">
                    <v-btn
                      v-if="!status.benchmark_running"
                      color="primary"
                      size="large"
                      prepend-icon="mdi-play"
                      elevation="2"
                      :loading="startingBenchmark"
                      @click="startBenchmark"
                    >
                      Uruchom Badanie Masowe
                    </v-btn>

                    <v-btn
                      v-else
                      color="error"
                      size="large"
                      prepend-icon="mdi-stop"
                      elevation="2"
                      @click="stopBenchmark"
                    >
                      Zatrzymaj Badanie
                    </v-btn>

                    <v-btn
                      variant="outlined"
                      size="large"
                      prepend-icon="mdi-refresh"
                      class="ml-2"
                      @click="fetchData"
                    >
                      Odśwież
                    </v-btn>
                  </div>
                </v-card>

                <!-- Live Log Terminal Stream -->
                <v-card border elevation="0" class="rounded-lg bg-surface-variant">
                  <v-card-title class="d-flex align-center text-subtitle-1 py-3 px-4 border-b">
                    <v-icon icon="mdi-console-line" class="mr-2 text-primary" size="20"></v-icon>
                    Konsola Zdarzeń Badania (Live Terminal Stream)
                    <v-spacer></v-spacer>
                    <v-btn variant="text" size="x-small" icon="mdi-delete-sweep" @click="liveLogs = []"></v-btn>
                  </v-card-title>
                  <div
                    class="pa-4 font-mono text-caption overflow-y-auto"
                    style="max-height: 280px; min-height: 180px; font-family: 'JetBrains Mono', monospace;"
                  >
                    <div v-if="liveLogs.length === 0" class="text-disabled">
                      Brak nowych zdarzeń. Uruchom zadanie lub pełne badanie, aby śledzić proces w czasie rzeczywistym.
                    </div>
                    <div v-for="(log, idx) in liveLogs" :key="idx" class="mb-1">
                      <span class="text-disabled">[{{ log.time }}]</span>
                      <v-chip size="x-small" :color="getLogColor(log.type)" class="mx-1" variant="tonal">
                        {{ log.type.toUpperCase() }}
                      </v-chip>
                      <span>{{ log.text }}</span>
                    </div>
                  </div>
                </v-card>
              </v-col>

              <!-- Quick Status & Overview -->
              <v-col cols="12" md="4">
                <v-card border elevation="0" class="pa-4 rounded-lg mb-4">
                  <div class="text-subtitle-1 font-weight-bold mb-3 d-flex align-center">
                    <v-icon icon="mdi-memory" color="primary" class="mr-2"></v-icon>
                    Aktywne Modele Ollama (RTX 5080)
                  </div>
                  <v-list density="compact" class="bg-transparent pa-0">
                    <v-list-item
                      v-for="model in status.ollama_models"
                      :key="model"
                      class="px-0 py-1"
                    >
                      <template v-slot:prepend>
                        <v-icon icon="mdi-checkbox-marked-circle-outline" color="success" size="18" class="mr-2"></v-icon>
                      </template>
                      <v-list-item-title class="font-mono text-body-2">{{ model }}</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-card>

                <v-card border elevation="0" class="pa-4 rounded-lg">
                  <div class="text-subtitle-1 font-weight-bold mb-2 d-flex align-center">
                    <v-icon icon="mdi-book-check-outline" color="secondary" class="mr-2"></v-icon>
                    Szybkie Akcje
                  </div>
                  <v-btn
                    block
                    variant="tonal"
                    color="primary"
                    class="mb-2"
                    prepend-icon="mdi-file-document-refresh-outline"
                    @click="generateReports"
                    :loading="generatingReports"
                  >
                    Generuj Raporty LaTeX & Excel
                  </v-btn>
                  <v-btn
                    block
                    variant="outlined"
                    class="mb-2"
                    prepend-icon="mdi-chart-areaspline"
                    @click="activeTab = 'results'"
                  >
                    Zobacz Wykresy (300 DPI)
                  </v-btn>
                  <v-btn
                    block
                    variant="outlined"
                    prepend-icon="mdi-file-code-outline"
                    @click="activeTab = 'thesis'"
                  >
                    Podgląd Rozdziału 5 (.tex / .md)
                  </v-btn>
                </v-card>
              </v-col>
            </v-row>
          </v-window-item>

          <!-- TAB 2: LABORATORIUM ZADANIA & INTERAKTYWNA DEBATA -->
          <v-window-item value="lab">
            <v-card border elevation="0" class="pa-5 rounded-lg mb-4">
              <v-row align="center">
                <v-col cols="12" md="4">
                  <v-select
                    v-model="selectedTaskId"
                    :items="tasks"
                    item-title="id"
                    item-value="id"
                    label="Wybierz zadanie badawcze"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                  >
                    <template v-slot:item="{ props, item }">
                      <v-list-item v-bind="props" :title="item.raw.id">
                        <template v-slot:subtitle>
                          {{ item.raw.category }} • Trudność: {{ item.raw.difficulty }} • Wymaga: {{ item.raw.required_tool }}
                        </template>
                        <template v-slot:append>
                          <v-chip v-if="item.raw.completed" size="x-small" color="success">Ukończono</v-chip>
                        </template>
                      </v-list-item>
                    </template>
                  </v-select>
                </v-col>

                <v-col cols="12" md="3">
                  <v-select
                    v-model="selectedExperimentMode"
                    :items="experimentModes"
                    item-title="title"
                    item-value="value"
                    label="Tryb Badawczy (Magisterski)"
                    density="comfortable"
                    variant="outlined"
                    hide-details
                  ></v-select>
                </v-col>
                <v-col v-if="selectedExperimentMode === 'ablation'" cols="12" md="2">
                  <v-select
                    v-model="selectedAblationVariant"
                    :items="ablationVariants"
                    item-title="title"
                    item-value="value"
                    label="Ablacja"
                    density="comfortable"
                    variant="outlined"
                    hide-details
                  ></v-select>
                </v-col>
                <v-col cols="12" :md="selectedExperimentMode === 'ablation' ? 3 : 5" class="d-flex justify-end">
                  <v-btn
                    color="primary"
                    size="large"
                    prepend-icon="mdi-play"
                    :loading="runningSingleTask"
                    @click="runSingleTask"
                  >
                    Uruchom Eksperyment
                  </v-btn>
                </v-col>
              </v-row>

              <!-- Selected Task Details Box -->
              <div v-if="currentTaskDetails" class="mt-4 pt-4 border-t">
                <v-row>
                  <v-col cols="12" md="8">
                    <div class="text-caption text-medium-emphasis text-uppercase font-weight-bold">
                      Treść Problemu Badawczego:
                    </div>
                    <div class="text-body-1 mt-1 font-weight-medium pa-3 rounded bg-surface-variant">
                      {{ currentTaskDetails.query }}
                    </div>
                  </v-col>
                  <v-col cols="12" md="4">
                    <div class="text-caption text-medium-emphasis text-uppercase font-weight-bold">
                      Wzorzec Obiektywny (Ground Truth):
                    </div>
                    <div class="text-body-2 mt-1 pa-3 rounded bg-surface-variant text-secondary">
                      {{ currentTaskDetails.expected_answer }}
                    </div>
                  </v-col>
                </v-row>
              </div>
            </v-card>

            <!-- Experiment Results View (Solo vs Swarm Debate) -->
            <div v-if="singleTaskResult">
              <!-- Academic Telemetry & Taxonomy Banner -->
              <v-card v-if="singleTaskResult.telemetry || singleTaskResult.failure_taxonomy" border elevation="0" class="pa-3 mb-4 rounded-lg bg-surface">
                <div class="d-flex flex-wrap align-center justify-space-between ga-2">
                  <div class="d-flex align-center ga-2">
                    <v-icon icon="mdi-chart-bell-curve-cumulative" color="accent"></v-icon>
                    <span class="text-caption font-weight-bold">Diagnoza Magisterska:</span>
                    <v-chip size="small" :color="singleTaskResult.failure_taxonomy?.includes('Sukces') ? 'success' : 'warning'" variant="tonal">
                      {{ singleTaskResult.failure_taxonomy || 'Brak błędu' }}
                    </v-chip>
                    <v-chip v-if="singleTaskResult.ablation_variant && singleTaskResult.ablation_variant !== 'full_swarm'" size="small" color="info" variant="outlined">
                      Ablacja: {{ singleTaskResult.ablation_variant }}
                    </v-chip>
                  </div>
                  <div v-if="singleTaskResult.telemetry" class="d-flex align-center ga-2">
                    <v-chip size="small" color="primary" variant="outlined">
                      Peak VRAM: {{ singleTaskResult.telemetry.peak_vram_mb }} MB
                    </v-chip>
                    <v-chip size="small" color="secondary" variant="outlined">
                      Przepustowość: {{ singleTaskResult.telemetry.tokens_per_second }} tok/s
                    </v-chip>
                  </div>
                </div>
              </v-card>
              <v-row class="mb-4">
                <!-- Solo Model Card -->
                <v-col cols="12" md="5">
                  <v-card border elevation="0" class="h-100 rounded-lg">
                    <v-card-title class="d-flex align-center border-b py-3 px-4 bg-surface-variant">
                      <v-icon icon="mdi-account" class="mr-2 text-medium-emphasis"></v-icon>
                      Solo Agent (ReAct)
                      <v-spacer></v-spacer>
                      <v-chip color="primary" size="small" class="font-weight-bold">
                        Wynik: {{ singleTaskResult.solo.score }} / 100
                      </v-chip>
                    </v-card-title>
                    <v-card-text class="pa-4">
                      <div class="d-flex text-caption text-medium-emphasis mb-3">
                        <span class="mr-3">⏱️ Czas: {{ singleTaskResult.solo.time }}s</span>
                        <span>🔤 Tokeny: {{ singleTaskResult.solo.tokens }}</span>
                      </div>
                      <div class="font-mono text-body-2 whitespace-pre-wrap pa-3 rounded bg-surface-variant">
                        {{ singleTaskResult.solo.final_answer }}
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>

                <!-- Multi-Agent Swarm Debate Card -->
                <v-col cols="12" md="7">
                  <v-card border elevation="0" class="h-100 rounded-lg">
                    <v-card-title class="d-flex align-center border-b py-3 px-4 bg-surface-variant">
                      <v-icon icon="mdi-account-group" class="mr-2 text-secondary"></v-icon>
                      Multi-Agent Swarm (Debata Roje)
                      <v-spacer></v-spacer>
                      <v-chip color="secondary" size="small" class="font-weight-bold">
                        Finał: {{ singleTaskResult.multi.score_final }} / 100
                      </v-chip>
                    </v-card-title>
                    <v-card-text class="pa-4">
                      <div class="d-flex text-caption text-medium-emphasis mb-3">
                        <span class="mr-3">⏱️ Czas: {{ singleTaskResult.multi.time }}s</span>
                        <span class="mr-3">🔤 Tokeny: {{ singleTaskResult.multi.tokens }}</span>
                        <span>🔄 Tury: {{ singleTaskResult.multi.turns ? singleTaskResult.multi.turns.length : 0 }}</span>
                      </div>

                      <!-- Step-by-Step Debate Chat Bubbles -->
                      <div class="debate-container overflow-y-auto pa-2" style="max-height: 480px;">
                        <div
                          v-for="(turn, tIdx) in singleTaskResult.multi.turns"
                          :key="tIdx"
                          class="mb-3 pa-3 rounded-lg border bg-surface"
                        >
                          <div class="d-flex align-center mb-1">
                            <v-icon :icon="getAgentIcon(turn.role)" :color="getAgentColor(turn.role)" class="mr-2" size="20"></v-icon>
                            <span class="font-weight-bold text-caption" :class="'text-' + getAgentColor(turn.role)">
                              Tura {{ turn.turn }}: {{ turn.role }}
                            </span>
                          </div>
                          <div class="text-body-2 whitespace-pre-wrap ml-6">
                            {{ turn.text }}
                          </div>
                          <div v-if="turn.tool_output" class="mt-2 ml-6 pa-2 rounded bg-surface-variant text-caption font-mono text-warning">
                            🛠️ Wykonanie Narzędzia:
                            <pre class="mt-1">{{ turn.tool_output }}</pre>
                          </div>
                        </div>
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>

              <!-- LLM Jury Verdict Box -->
              <v-card border elevation="0" class="rounded-lg pa-4 bg-surface-variant border-warning">
                <div class="d-flex align-center mb-2">
                  <v-icon icon="mdi-gavel" color="warning" class="mr-2" size="24"></v-icon>
                  <span class="text-subtitle-1 font-weight-bold">
                    Werdykt Panelu Sędziowskiego (LLM-as-a-Jury): Microsoft Phi-4 • Alibaba Qwen 2.5 • Mistral-NeMo
                  </span>
                </div>
                <div class="text-body-2 font-italic mt-1 font-weight-medium">
                  {{ singleTaskResult.jury.reasons }}
                </div>
              </v-card>
            </div>
          </v-window-item>

          <!-- TAB 3: KONFIGURACJA AGENTÓW I MODELI -->
          <v-window-item value="agents">
            <v-card border elevation="0" class="pa-5 rounded-lg mb-4">
              <div class="d-flex align-center justify-space-between mb-4">
                <div>
                  <div class="text-h6 font-weight-bold">Role Kognitywne i Przypisanie Modeli LLM</div>
                  <div class="text-caption text-medium-emphasis">
                    Dostosuj modele dla RTX 5080 (16 GB) oraz prompty systemowe poszczególnych agentów
                  </div>
                </div>
                <div class="d-flex ga-2">
                  <v-btn
                    color="secondary"
                    variant="tonal"
                    prepend-icon="mdi-download"
                    @click="openModelDialog"
                  >
                    Pobierz model Ollama
                  </v-btn>
                  <v-btn
                    color="primary"
                    prepend-icon="mdi-content-save-outline"
                    :loading="savingAgents"
                    @click="saveAgentsConfig"
                  >
                    Zapisz Konfigurację
                  </v-btn>
                </div>
              </div>

              <v-row>
                <v-col
                  v-for="(agent, aIdx) in agentsList"
                  :key="agent.id"
                  cols="12"
                  md="6"
                  lg="4"
                >
                  <v-card border elevation="0" class="pa-4 rounded-lg h-100 bg-surface">
                    <div class="d-flex align-center mb-2">
                      <v-icon :icon="getAgentIcon(agent.role)" :color="getAgentColor(agent.role)" class="mr-2" size="24"></v-icon>
                      <div>
                        <div class="font-weight-bold text-subtitle-2">{{ agent.role }}</div>
                        <div class="text-caption text-disabled font-mono">id: {{ agent.id }}</div>
                      </div>
                    </div>

                    <v-text-field
                      v-model="agent.model"
                      label="Model LLM (Ollama)"
                      density="compact"
                      variant="outlined"
                      class="mt-2 mb-2 font-mono"
                      hide-details
                    ></v-text-field>

                    <v-textarea
                      v-model="agent.system_prompt"
                      label="Prompt Systemowy"
                      density="compact"
                      variant="outlined"
                      rows="4"
                      hide-details
                      class="text-caption"
                    ></v-textarea>
                  </v-card>
                </v-col>
              </v-row>
            </v-card>
          </v-window-item>

          <!-- TAB 4: WYNIKI & WYKRESY -->
          <v-window-item value="results">
            <!-- Results Data Table -->
            <v-card border elevation="0" class="pa-4 rounded-lg mb-6">
              <div class="d-flex align-center justify-space-between mb-4">
                <div>
                  <div class="text-h6 font-weight-bold">Szczegółowa Tabela Pomiarów</div>
                  <div class="text-caption text-medium-emphasis">
                    Wszystkie ukończone zadania badawcze zapisane w checkpoint.jsonl
                  </div>
                </div>
                <v-text-field
                  v-model="tableSearch"
                  prepend-inner-icon="mdi-magnify"
                  label="Szukaj zadania..."
                  density="compact"
                  variant="outlined"
                  hide-details
                  style="max-width: 280px;"
                ></v-text-field>
              </div>

              <v-table density="comfortable" hover>
                <thead>
                  <tr>
                    <th class="text-left">ID Zadania</th>
                    <th class="text-left">Kategoria</th>
                    <th class="text-left">Trudność</th>
                    <th class="text-center">Solo Score</th>
                    <th class="text-center">Multi (Fin)</th>
                    <th class="text-center">Zysk Debaty</th>
                    <th class="text-center">Czas Solo</th>
                    <th class="text-center">Czas Multi</th>
                    <th class="text-right">Koszt USD</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in filteredTableResults" :key="row.task_id">
                    <td class="font-mono text-body-2 font-weight-medium">{{ row.task_id }}</td>
                    <td>
                      <v-chip size="x-small" variant="tonal">{{ row.category }}</v-chip>
                    </td>
                    <td>
                      <v-chip size="x-small" :color="getDifficultyColor(row.difficulty)">
                        {{ row.difficulty }}
                      </v-chip>
                    </td>
                    <td class="text-center font-weight-bold">{{ row.score_solo }}</td>
                    <td class="text-center font-weight-bold text-secondary">{{ row.score_multi_final }}</td>
                    <td class="text-center font-weight-medium" :class="row.debate_gain >= 0 ? 'text-secondary' : 'text-error'">
                      {{ row.debate_gain > 0 ? '+' : '' }}{{ row.debate_gain }}
                    </td>
                    <td class="text-center text-caption">{{ row.solo_time }}s</td>
                    <td class="text-center text-caption">{{ row.multi_time }}s</td>
                    <td class="text-right font-mono text-caption">${{ row.multi_cost_usd?.toFixed(4) }}</td>
                  </tr>
                  <tr v-if="filteredTableResults.length === 0">
                    <td colspan="9" class="text-center pa-6 text-disabled">
                      Brak rekordów. Uruchom zadania, aby zapełnić tabelę.
                    </td>
                  </tr>
                </tbody>
              </v-table>
            </v-card>

            <!-- Publication Figures (300 DPI) Gallery -->
            <v-card border elevation="0" class="pa-4 rounded-lg">
              <div class="text-h6 font-weight-bold mb-1">Wykresy Publikacyjne do Pracy Inżynierskiej (300 DPI)</div>
              <div class="text-caption text-medium-emphasis mb-4">
                Wygenerowane automatycznie przez Seaborn & Matplotlib do wklejenia w pracy
              </div>

              <v-row>
                <v-col
                  v-for="fig in figuresList"
                  :key="fig"
                  cols="12"
                  md="6"
                >
                  <v-card border elevation="0" class="pa-2 rounded-lg bg-surface">
                    <div class="text-subtitle-2 font-weight-bold pa-2">{{ fig }}</div>
                    <div class="figure-container rounded pa-2 bg-surface-variant">
                      <v-img
                        :src="'/api/figures/' + fig"
                        contain
                        max-height="450"
                        class="rounded cursor-pointer"
                        @click="openImage('/api/figures/' + fig)"
                      ></v-img>
                    </div>
                  </v-card>
                </v-col>
              </v-row>
            </v-card>
          </v-window-item>

          <!-- TAB 5: PRACA INŻYNIERSKA (ROZDZIAŁ 5 & LATEX) -->
          <v-window-item value="thesis">
            <v-card border elevation="0" class="pa-5 rounded-lg mb-4">
              <div class="d-flex align-center justify-space-between mb-4">
                <div>
                  <div class="text-h6 font-weight-bold">Rozdział 5: Wyniki Badań i Dyskusja</div>
                  <div class="text-caption text-medium-emphasis">
                    Automatycznie zredagowany tekst analizy statystycznej gotowy do wklejenia w pracy (.tex / .md)
                  </div>
                </div>
                <div class="d-flex align-center ga-2">
                  <v-btn-toggle v-model="thesisTabMode" mandatory density="compact" color="primary" class="mr-2">
                    <v-btn value="chapter" prepend-icon="mdi-book-open-page-variant">Rozdział 5 (Wyniki)</v-btn>
                    <v-btn value="methodology" prepend-icon="mdi-school">Metodologia Magisterska</v-btn>
                  </v-btn-toggle>
                  <v-btn
                    color="primary"
                    prepend-icon="mdi-refresh"
                    :loading="generatingReports"
                    @click="generateReports"
                  >
                    Przebuduj Raporty
                  </v-btn>
                </div>
              </div>

              <v-card border elevation="0" class="pa-4 rounded-lg bg-surface-variant">
                <pre class="whitespace-pre-wrap font-sans text-body-2 leading-relaxed" style="font-family: inherit;">
{{ thesisTabMode === "chapter" ? thesisChapterText : thesisMethodologyText }}
                </pre>
              </v-card>
            </v-card>
          </v-window-item>
        </v-window>
      </v-container>
    </v-main>

    <!-- Ollama Models Dialog -->
    <v-dialog v-model="modelDialog" max-width="720px">
      <v-card border elevation="0" class="rounded-lg bg-surface">
        <v-card-title class="d-flex align-center justify-space-between pa-4 border-b">
          <div class="d-flex align-center font-weight-bold">
            <v-icon icon="mdi-server-network" color="primary" class="mr-2"></v-icon>
            Zarządzanie Modelami Ollama (Lokalne LLM)
          </div>
          <v-btn icon="mdi-close" variant="text" size="small" @click="modelDialog = false"></v-btn>
        </v-card-title>

        <v-card-text class="pa-4">
          <!-- Pull Input Form -->
          <div class="text-subtitle-2 font-weight-bold mb-2">Pobierz nowy model do lokalnej Ollamy</div>
          <div class="text-caption text-medium-emphasis mb-3">
            Wpisz tag modelu z biblioteki ollama.com (np. <code class="px-1 py-0.5 rounded bg-surface-variant font-mono">phi4:latest</code>, <code class="px-1 py-0.5 rounded bg-surface-variant font-mono">deepseek-r1:14b</code>, <code class="px-1 py-0.5 rounded bg-surface-variant font-mono">qwen2.5-coder:14b</code>).
          </div>

          <v-row dense class="align-center mb-2">
            <v-col cols="12" sm="8">
              <v-text-field
                v-model="modelToPull"
                placeholder="np. phi4:latest lub mistral-nemo:12b"
                density="compact"
                variant="outlined"
                hide-details
                prepend-inner-icon="mdi-tag-outline"
                @keyup.enter="pullModel(modelToPull)"
              ></v-text-field>
            </v-col>
            <v-col cols="12" sm="4">
              <v-btn
                block
                color="primary"
                prepend-icon="mdi-download"
                :loading="pullingModel"
                :disabled="!modelToPull"
                @click="pullModel(modelToPull)"
              >
                Pobierz model
              </v-btn>
            </v-col>
          </v-row>

          <v-alert
            v-if="pullStatus"
            :type="pullStatus.type"
            density="compact"
            variant="tonal"
            class="mb-4 mt-2"
          >
            {{ pullStatus.message }}
          </v-alert>

          <v-divider class="my-4"></v-divider>

          <!-- Recommended Models List -->
          <div class="d-flex align-center justify-space-between mb-3">
            <div class="text-subtitle-2 font-weight-bold">
              Rekomendowane modele dla architektury Roju (RTX 5080 16 GB)
            </div>
            <v-btn
              variant="text"
              size="small"
              icon="mdi-refresh"
              :loading="loadingOllamaModels"
              @click="fetchOllamaModels"
              title="Odśwież listę modeli"
            ></v-btn>
          </div>

          <v-list density="compact" lines="two" class="bg-surface-variant rounded-lg pa-1 mb-4">
            <v-list-item
              v-for="m in recommendedModels"
              :key="m.name"
              class="rounded mb-1"
            >
              <template #prepend>
                <v-icon
                  :icon="isModelInstalled(m.name) ? 'mdi-check-circle' : 'mdi-download-outline'"
                  :color="isModelInstalled(m.name) ? 'success' : 'medium-emphasis'"
                  class="mr-2"
                ></v-icon>
              </template>
              <v-list-item-title class="font-weight-bold font-mono text-body-2">
                {{ m.name }}
                <v-chip size="x-small" color="primary" variant="outlined" class="ml-2 font-sans font-weight-regular">
                  {{ m.size }}
                </v-chip>
              </v-list-item-title>
              <v-list-item-subtitle class="text-caption">
                {{ m.desc }} • <span class="text-medium-emphasis">Rola: {{ m.role }}</span>
              </v-list-item-subtitle>
              <template #append>
                <v-chip
                  v-if="isModelInstalled(m.name)"
                  size="small"
                  color="success"
                  variant="tonal"
                >
                  Zainstalowany
                </v-chip>
                <v-btn
                  v-else
                  size="small"
                  color="primary"
                  variant="tonal"
                  prepend-icon="mdi-download"
                  :loading="pullingModel && currentPullingName === m.name"
                  @click="pullModel(m.name)"
                >
                  Pobierz
                </v-btn>
              </template>
            </v-list-item>
          </v-list>

          <!-- Installed Models List -->
          <div class="text-subtitle-2 font-weight-bold mb-2">
            Zainstalowane modele w lokalnej Ollamie ({{ installedModels.length }})
          </div>
          <div class="d-flex flex-wrap ga-2">
            <v-chip
              v-for="name in installedModels"
              :key="name"
              size="small"
              color="accent"
              variant="tonal"
              class="font-mono"
            >
              <v-icon start icon="mdi-robot"></v-icon>
              {{ name }}
            </v-chip>
            <div v-if="installedModels.length === 0" class="text-caption text-medium-emphasis">
              Brak wykrytych modeli lub Ollama jest offline.
            </div>
          </div>
        </v-card-text>

        <v-card-actions class="pa-4 border-t justify-end">
          <v-btn variant="text" @click="modelDialog = false">Zamknij</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Global Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000" location="bottom right">
      {{ snackbar.text }}
    </v-snackbar>
  </v-app>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'

const theme = ref('dark')
const modelDialog = ref(false)
const modelToPull = ref('')
const pullingModel = ref(false)
const currentPullingName = ref('')
const pullStatus = ref(null)
const loadingOllamaModels = ref(false)
const installedModels = ref([])
const recommendedModels = ref([
  { name: 'phi4:latest', desc: 'Microsoft Phi-4 (14B) - Logika i wnioskowanie naukowe', role: 'Solver / Jury', size: '9.1 GB' },
  { name: 'deepseek-r1:14b', desc: 'DeepSeek-R1 (14B) - Rozumowanie łańcuchowe (CoT)', role: "Devil's Advocate", size: '9.0 GB' },
  { name: 'qwen2.5-coder:14b', desc: 'Qwen 2.5 Coder (14B) - Kod i debugowanie', role: 'Coder / QA Engineer', size: '9.0 GB' },
  { name: 'mistral-nemo:12b', desc: 'Mistral-NeMo (12B) - Wyszukiwanie i sędzia LLM', role: 'Archivist / Jury', size: '7.1 GB' },
  { name: 'qwen2.5:14b', desc: 'Qwen 2.5 (14B) - Moderacja dyskusji', role: 'Orchestrator / Critic', size: '9.0 GB' },
  { name: 'llama3.1:8b', desc: 'Meta Llama 3.1 (8B) - Synteza końcowa', role: 'Secretary', size: '4.7 GB' },
  { name: 'gemma2:9b', desc: 'Google Gemma 2 (9B) - Ekstrakcja faktów', role: 'Analyst', size: '5.4 GB' }
])

function isModelInstalled(name) {
  const norm = (n) => n.includes(':') ? n : `${n}:latest`
  return installedModels.value.some(m => norm(m) === norm(name) || m.startsWith(name))
}

async function fetchOllamaModels() {
  loadingOllamaModels.value = true
  try {
    const res = await axios.get('/api/ollama/models')
    if (res.data) {
      installedModels.value = res.data.installed || []
      if (res.data.recommended && res.data.recommended.length > 0) {
        recommendedModels.value = res.data.recommended
      }
    }
  } catch (err) {
    console.error('Błąd pobierania modeli Ollama:', err)
  } finally {
    loadingOllamaModels.value = false
  }
}

function openModelDialog() {
  modelDialog.value = true
  pullStatus.value = null
  fetchOllamaModels()
}

async function pullModel(name) {
  if (!name) return
  pullingModel.value = true
  currentPullingName.value = name
  pullStatus.value = { type: 'info', message: `Rozpoczęto pobieranie modelu '${name}' do lokalnej Ollamy. To może potrwać kilka minut...` }
  try {
    const res = await axios.post('/api/ollama/pull', { model: name })
    pullStatus.value = { type: 'success', message: res.data.message || `Model '${name}' został pomyślnie pobrany!` }
    showToast(`Pobrano model ${name}!`, 'success')
    await fetchOllamaModels()
    await fetchData()
  } catch (err) {
    pullStatus.value = {
      type: 'error',
      message: err.response?.data?.detail || `Błąd podczas pobierania modelu '${name}'`
    }
    showToast(`Błąd pobierania ${name}`, 'error')
  } finally {
    pullingModel.value = false
    currentPullingName.value = ''
  }
}
const activeTab = ref('dashboard')
const selectedProvider = ref('ollama')
const providers = ['ollama', 'groq', 'openai', 'openrouter']

const status = ref({
  benchmark_running: false,
  completed_count: 0,
  total_count: 35,
  current_step: '',
  ollama_online: false,
  ollama_models: []
})

const stats = ref({})
const tasks = ref([])
const agentsList = ref([])
const figuresList = ref([])
const resultsList = ref([])
const thesisChapterText = ref('')
const liveLogs = ref([
  { time: '14:17:22', type: 'completed', text: 'Zapisano checkpoint: task_01_helium | Solo: 91.7 pkt, Swarm: 100.0 pkt (Zysk: +8.3 pkt)' },
  { time: '14:15:10', type: 'info', text: 'LLM Jury konsensus osiągnięty (Phi-4: 100, Qwen-2.5: 100, Mistral-NeMo: 100)' },
  { time: '14:13:53', type: 'task_start', text: 'Uruchomiono zadanie [1/35]: task_01_helium (Kategoria: physics_commonsense)' },
  { time: '14:13:50', type: 'info', text: 'Inicjalizacja silnika badawczego na NVIDIA RTX 5080 (16 GB GDDR7)' }
])

const filterCategory = ref('Wszystkie kategorie')
const filterDifficulty = ref('Wszystkie trudności')
const resumeCheckpoint = ref(true)
const dryRun = ref(false)
const selectedTaskId = ref('task_01_helium')
const selectedExperimentMode = ref('full')
const experimentModes = [
  { value: 'full', title: 'Solo ReAct vs Swarm (Domyślny)' },
  { value: 'reflexion', title: 'Solo Reflexion (Samo-krytyka)' },
  { value: 'best_of_n', title: 'Solo Best-of-3 (Self-Consistency)' },
  { value: 'ablation', title: 'Badanie Ablacyjne (Ablation)' }
]
const selectedAblationVariant = ref('full_swarm')
const ablationVariants = [
  { value: 'full_swarm', title: 'Pełny Rój (10 ról)' },
  { value: 'no_devil', title: "Rój bez Devil's Advocate" },
  { value: 'no_fact_checker', title: 'Rój bez Fact-Checkera i Security' },
  { value: 'no_coder_qa', title: 'Czysty Rozum (Bez Kodu)' },
  { value: 'minimal_triad', title: 'Minimalna Triada (3 Agentów)' }
]
const thesisTabMode = ref('chapter')
const thesisMethodologyText = ref('')
const singleTaskResult = ref(null)
const tableSearch = ref('')

const startingBenchmark = ref(false)
const runningSingleTask = ref(false)
const savingAgents = ref(false)
const generatingReports = ref(false)
const snackbar = ref({ show: false, text: '', color: 'success' })

let eventSource = null

function showToast(text, color = 'success') {
  snackbar.value = { show: true, text, color }
}

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
}

const categories = computed(() => {
  return [...new Set(tasks.value.map(t => t.category).filter(Boolean))].sort()
})

const currentTaskDetails = computed(() => {
  return tasks.value.find(t => t.id === selectedTaskId.value)
})

const filteredTableResults = computed(() => {
  if (!tableSearch.value) return resultsList.value
  const q = tableSearch.value.toLowerCase()
  return resultsList.value.filter(r =>
    r.task_id?.toLowerCase().includes(q) ||
    r.category?.toLowerCase().includes(q)
  )
})

function getDifficultyColor(diff) {
  if (diff === 'easy') return 'success'
  if (diff === 'medium') return 'warning'
  if (diff === 'hard') return 'error'
  return 'default'
}

function getLogColor(type) {
  if (type === 'error') return 'error'
  if (type === 'task_start') return 'primary'
  if (type === 'completed') return 'success'
  return 'info'
}

function getAgentIcon(role) {
  const r = role.toLowerCase()
  if (r.includes('orchestrator') || r.includes('manager')) return 'mdi-brain'
  if (r.includes('analyst')) return 'mdi-magnify'
  if (r.includes('archivist')) return 'mdi-database'
  if (r.includes('coder') || r.includes('developer')) return 'mdi-code-braces'
  if (r.includes('qa') || r.includes('debugger')) return 'mdi-bug-check'
  if (r.includes('security')) return 'mdi-shield-check'
  if (r.includes('fact')) return 'mdi-scale-balance'
  if (r.includes('solver') || r.includes('logician')) return 'mdi-lightbulb-on'
  if (r.includes('devil')) return 'mdi-emoticon-devil'
  if (r.includes('critic')) return 'mdi-check-decagram'
  if (r.includes('secretary')) return 'mdi-text-box-check'
  return 'mdi-account'
}

function getAgentColor(role) {
  const r = role.toLowerCase()
  if (r.includes('coder') || r.includes('developer')) return 'success'
  if (r.includes('devil')) return 'error'
  if (r.includes('solver')) return 'warning'
  if (r.includes('security')) return 'accent'
  return 'primary'
}

async function fetchData() {
  try {
    const [statusRes, tasksRes, agentsRes, resultsRes, figuresRes, chapterRes] = await Promise.all([
      axios.get('/api/status'),
      axios.get('/api/tasks'),
      axios.get('/api/agents'),
      axios.get('/api/results'),
      axios.get('/api/figures'),
      axios.get('/api/reports/chapter')
    ])

    status.value = statusRes.data
    tasks.value = tasksRes.data
    agentsList.value = agentsRes.data
    resultsList.value = resultsRes.data.records || []
    stats.value = resultsRes.data.statistics || {}
    figuresList.value = figuresRes.data || []
    thesisChapterText.value = chapterRes.data.content || ''
    try {
      const methRes = await axios.get('/api/reports/thesis-methodology')
      thesisMethodologyText.value = methRes.data.content || ''
    } catch (e) {}
    await fetchOllamaModels()
    if (!singleTaskResult.value && selectedTaskId.value) {
      await loadTaskResult(selectedTaskId.value)
    }
  } catch (err) {
    console.error('Błąd pobierania danych:', err)
  }
}


async function loadTaskResult(taskId) {
  try {
    const res = await axios.get(`/api/interactive/task/${taskId}`)
    if (res.data) {
      singleTaskResult.value = res.data
    }
  } catch (err) {}
}

watch(selectedTaskId, (newVal) => {
  if (newVal) {
    loadTaskResult(newVal)
  }
})

function initSSE() {
  if (eventSource) eventSource.close()
  eventSource = new EventSource('/api/benchmark/stream')
  eventSource.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data)
      const now = new Date().toLocaleTimeString()
      if (msg.type === 'init' || msg.type === 'status') {
        status.value.benchmark_running = msg.data.running
        status.value.current_step = msg.data.step
      } else if (msg.type === 'task_start') {
        status.value.current_task = msg.data.task_id
        liveLogs.value.unshift({ time: now, type: 'task', text: `Uruchomiono zadanie [${msg.data.index}/${msg.data.total}]: ${msg.data.task_id}` })
      } else if (msg.type === 'completed') {
        status.value.benchmark_running = false
        liveLogs.value.unshift({ time: now, type: 'completed', text: 'Zakończono pełną serię badania!' })
        fetchData()
      } else if (msg.type === 'error') {
        liveLogs.value.unshift({ time: now, type: 'error', text: `Błąd: ${msg.data.error}` })
      }
    } catch (err) {}
  }
}

async function startBenchmark() {
  startingBenchmark.value = true
  try {
    const cat = filterCategory.value !== 'Wszystkie kategorie' ? filterCategory.value : null
    const diff = filterDifficulty.value !== 'Wszystkie trudności' ? filterDifficulty.value : null
    await axios.post('/api/benchmark/start', {
      provider: selectedProvider.value,
      category: cat,
      difficulty: diff,
      resume: resumeCheckpoint.value,
      dry_run: dryRun.value
    })
    showToast('Rozpoczęto badanie w tle!', 'primary')
    fetchData()
  } catch (err) {
    showToast(err.response?.data?.detail || 'Błąd startu badania', 'error')
  } finally {
    startingBenchmark.value = false
  }
}

async function stopBenchmark() {
  try {
    await axios.post('/api/benchmark/stop')
    showToast('Wysłano sygnał zatrzymania', 'warning')
    fetchData()
  } catch (err) {
    showToast('Błąd zatrzymywania', 'error')
  }
}

async function runSingleTask() {
  runningSingleTask.value = true
  try {
    const res = await axios.post('/api/interactive/run-task', {
      task_id: selectedTaskId.value,
      provider: selectedProvider.value,
      mode: selectedExperimentMode.value,
      ablation_variant: selectedAblationVariant.value
    })
    singleTaskResult.value = res.data
    showToast(`Ukończono eksperyment dla ${selectedTaskId.value}!`, 'success')
    fetchData()
  } catch (err) {
    showToast(err.response?.data?.detail || 'Błąd wykonywania zadania', 'error')
  } finally {
    runningSingleTask.value = false
  }
}

async function saveAgentsConfig() {
  savingAgents.value = true
  try {
    await axios.put('/api/agents', agentsList.value)
    showToast('Zapisano pomyślnie konfigurację agentów!', 'success')
  } catch (err) {
    showToast('Błąd zapisu agentów', 'error')
  } finally {
    savingAgents.value = false
  }
}

async function generateReports() {
  generatingReports.value = true
  try {
    const res = await axios.post('/api/reports/generate')
    showToast('Wygenerowano rozdział Markdown, tabele LaTeX i wykresy!', 'success')
    fetchData()
  } catch (err) {
    showToast(err.response?.data?.detail || 'Błąd generowania raportów', 'error')
  } finally {
    generatingReports.value = false
  }
}

function openImage(url) {
  window.open(url, '_blank')
}

onMounted(() => {
  fetchData()
  initSSE()
})

onUnmounted(() => {
  if (eventSource) eventSource.close()
})
</script>

<style>
/* Global theme color enforcement */
.v-application {
  color: rgb(var(--v-theme-on-surface)) !important;
}

.bg-surface-variant {
  color: rgb(var(--v-theme-on-surface-variant)) !important;
}

.bg-surface {
  color: rgb(var(--v-theme-on-surface)) !important;
}

pre, code, .font-mono {
  color: inherit !important;
}

.debate-container {
  scrollbar-width: thin;
}

.whitespace-pre-wrap {
  white-space: pre-wrap;
  word-break: break-word;
}

.figure-container {
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background-color: rgba(255, 255, 255, 0.05);
}
</style>
