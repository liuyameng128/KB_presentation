<template>
  <div class="statistics-container">
    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-number">6298</div>
        <div class="stat-label">知识总条目数</div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-number">18</div>
        <div class="stat-label">今日新增知识</div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-number">126</div>
        <div class="stat-label">近7天新增</div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-number">482</div>
        <div class="stat-label">近30天新增</div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-number">6090</div>
        <div class="stat-label">自动导入</div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-number">208</div>
        <div class="stat-label">手动录入</div>
      </el-card>
    </div>

    <!-- 今日新增知识列表 -->
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="title">📋 今日新增知识列表</span>
          <el-button @click="refreshTodayKnowledge" :loading="todayLoading" size="small">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>
      </template>

      <el-table :data="todayKnowledgeList" v-loading="todayLoading" border stripe>
        <el-table-column type="index" label="序号" width="70" />
        <el-table-column prop="equipment" label="设备名称" width="180" show-overflow-tooltip />
        <el-table-column prop="phenomenon" label="故障现象" show-overflow-tooltip />
        <el-table-column prop="source_type" label="录入方式" width="110" />
        <el-table-column prop="file_name" label="来源文件" width="180" show-overflow-tooltip />
        <el-table-column prop="create_time" label="创建时间" width="180" />
      </el-table>

      <div v-if="todayKnowledgeList.length === 0 && !todayLoading" class="empty-tip">
        📭 暂无今日新增知识
      </div>
    </el-card>

    <!-- 入库方式统计 -->
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="title">📊 知识录入方式统计</span>
          <el-button @click="refreshImportStats" :loading="importLoading" size="small">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>
      </template>

      <el-table :data="importStats" v-loading="importLoading" border stripe>
        <el-table-column type="index" label="序号" width="70" />
        <el-table-column prop="type" label="录入方式" />
        <el-table-column prop="count" label="数量" width="160" />
        <el-table-column prop="ratio" label="占比" width="160" />
      </el-table>
    </el-card>

    <!-- 热点词汇 -->
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="title">🔥 热点设备与故障词汇</span>
          <el-button @click="refreshHotWords" :loading="hotwordLoading" size="small">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>
      </template>

      <div class="hotword-box" v-loading="hotwordLoading">
        <el-tag
          v-for="(item, index) in hotWords"
          :key="index"
          class="hotword-tag"
          :size="item.level"
          effect="plain"
        >
          {{ item.word }}（{{ item.count }}）
        </el-tag>
      </div>

      <div v-if="hotWords.length === 0 && !hotwordLoading" class="empty-tip">
        📭 暂无热点词汇数据
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'

const todayKnowledgeList = ref([])
const importStats = ref([])
const hotWords = ref([])

const todayLoading = ref(false)
const importLoading = ref(false)
const hotwordLoading = ref(false)

// 今日新增知识 mock 数据
const mockTodayKnowledgeList = [
  {
    equipment: '锅炉给水泵',
    phenomenon: '运行过程中出口压力波动较大',
    source_type: '自动导入',
    file_name: '锅炉运行规程.pdf',
    create_time: '2026-04-16 08:21:15'
  },
  {
    equipment: '汽轮机',
    phenomenon: '轴承温度异常升高',
    source_type: '手动录入',
    file_name: '人工新增',
    create_time: '2026-04-16 09:12:44'
  },
  {
    equipment: '发电机',
    phenomenon: '定子绕组温度偏高',
    source_type: '自动导入',
    file_name: '发电机检修记录.docx',
    create_time: '2026-04-16 10:05:37'
  },
  {
    equipment: '引风机',
    phenomenon: '运行振动超标',
    source_type: '自动导入',
    file_name: '风机故障案例汇总.doc',
    create_time: '2026-04-16 11:18:09'
  },
  {
    equipment: '凝结水泵',
    phenomenon: '泵体异响且流量下降',
    source_type: '手动录入',
    file_name: '人工新增',
    create_time: '2026-04-16 13:26:18'
  }
]

// 录入方式统计 mock 数据
const mockImportStats = [
  { type: '自动导入', count: 6090, ratio: '96.7%' },
  { type: '手动录入', count: 208, ratio: '3.3%' }
]

// 热点词汇 mock 数据
const mockHotWords = [
  { word: '锅炉', count: 186, level: 'large' },
  { word: '汽轮机', count: 152, level: 'large' },
  { word: '发电机', count: 138, level: 'large' },
  { word: '轴承温度高', count: 94, level: 'default' },
  { word: '振动超标', count: 88, level: 'default' },
  { word: '压力波动', count: 76, level: 'default' },
  { word: '油温异常', count: 63, level: 'small' },
  { word: '真空下降', count: 58, level: 'small' },
  { word: '保护动作', count: 55, level: 'small' },
  { word: '泄漏', count: 49, level: 'small' }
]

const refreshTodayKnowledge = () => {
  todayLoading.value = true
  setTimeout(() => {
    todayKnowledgeList.value = [...mockTodayKnowledgeList]
    todayLoading.value = false
  }, 500)
}

const refreshImportStats = () => {
  importLoading.value = true
  setTimeout(() => {
    importStats.value = [...mockImportStats]
    importLoading.value = false
  }, 400)
}

const refreshHotWords = () => {
  hotwordLoading.value = true
  setTimeout(() => {
    hotWords.value = [...mockHotWords]
    hotwordLoading.value = false
  }, 400)
}

onMounted(() => {
  refreshTodayKnowledge()
  refreshImportStats()
  refreshHotWords()
})
</script>

<style scoped>
.statistics-container {
  padding: 20px;
}

.stats-cards {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.stat-card {
  flex: 1;
  min-width: 150px;
  text-align: center;
  cursor: pointer;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  color: #007acc;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 8px;
}

.table-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 16px;
  font-weight: bold;
}

.empty-tip {
  text-align: center;
  padding: 40px;
  color: #999;
}

.hotword-box {
  min-height: 120px;
  padding: 10px 0;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.hotword-tag {
  margin-right: 6px;
  margin-bottom: 8px;
}
</style>