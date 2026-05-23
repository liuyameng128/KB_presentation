<template>
  <div class="wordcloud-container">
    <el-card shadow="never">
      <template #header>
        <div class="header">
          <span class="title">📊 热点问题词云</span>
          <el-button @click="refreshData" :loading="loading" size="small">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>
      </template>
      
      <div class="chart-container">
        <div v-if="loading" class="loading-tip">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>加载中...</span>
        </div>
        <div v-else id="wordcloud-chart" style="width: 100%; height: 550px;"></div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import 'echarts-wordcloud'
import { Refresh, Loading } from '@element-plus/icons-vue'

const loading = ref(false)
let chart = null

// const mockWordData = [
//   { name: '锅炉', value: 85 },
//   { name: '水冷壁', value: 72 },
//   { name: '轴承温度', value: 68 },
//   { name: '温度过高', value: 55 },
//   { name: '变压器', value: 52 },
//   { name: '油温', value: 48 },
//   { name: '断路器', value: 45 },
//   { name: '跳闸', value: 42 },
//   { name: '振动', value: 38 },
//   { name: '泄漏', value: 35 },
//   { name: '压力异常', value: 32 },
//   { name: '风机', value: 30 },
//   { name: '电机', value: 28 },
//   { name: '轴承', value: 25 },
//   { name: '绝缘', value: 22 },
//   { name: '过载', value: 20 },
//   { name: '短路', value: 18 },
//   { name: '接地', value: 16 },
//   { name: '保护动作', value: 15 },
//   { name: '控制系统', value: 14 }
// ]
  const mockWordData = [
    { name: '锅炉', value: 85 },
    { name: '水冷壁', value: 78 },
    { name: '轴承温度', value: 72 },
    { name: '爆管', value: 68 },
    { name: '温度过高', value: 65 },
    { name: '变压器', value: 62 },
    { name: '油温', value: 58 },
    { name: '断路器', value: 55 },
    { name: '跳闸', value: 52 },
    { name: '振动', value: 48 },
    { name: '泄漏', value: 45 },
    { name: '压力异常', value: 42 },
    { name: '风机', value: 40 },
    { name: '电机', value: 38 },
    { name: '轴承', value: 35 },
    { name: '过热变形', value: 32 },
    { name: '裂纹', value: 30 },
    { name: '冲蚀', value: 28 },
    { name: '无法停机', value: 26 },
    { name: '卡涩', value: 25 },
    { name: '高压加热器', value: 24 },
    { name: '动态超限', value: 22 },
    { name: '疏水不畅', value: 20 },
    { name: '再热器', value: 18 },
    { name: '绝缘', value: 22 },
    { name: '过载', value: 20 },
    { name: '短路', value: 18 },
    { name: '接地', value: 16 },
    { name: '保护动作', value: 15 },
    { name: '控制系统', value: 14 },
    { name: '磨煤机', value: 60 },
    { name: '堵磨', value: 55 },
    { name: '给煤机', value: 42 },
    { name: '排烟温度', value: 38 },
    { name: '空预器', value: 35 },
    { name: '积灰', value: 32 },
    { name: '结焦', value: 30 },
    { name: '汽轮机', value: 48 },
    { name: '轴向位移', value: 32 },
    { name: '推力瓦', value: 28 },
    { name: '凝汽器', value: 35 },
    { name: '真空下降', value: 30 },
    { name: '除氧器', value: 28 },
    { name: '溶解氧', value: 22 },
    { name: '发电机', value: 40 },
    { name: '转子接地', value: 25 },
    { name: '励磁', value: 20 },
    { name: '给水泵', value: 38 },
    { name: '循环泵', value: 32 },
    { name: '浆液循环泵', value: 28 },
    { name: '石灰石', value: 22 },
    { name: '脱硫', value: 35 },
    { name: '脱硝', value: 28 },
    { name: '电除尘', value: 25 },
    { name: '引风机', value: 38 },
    { name: '送风机', value: 32 },
    { name: '一次风机', value: 30 }
  ]
const refreshData = async () => {
  loading.value = true
  setTimeout(() => {
    renderChart()
    loading.value = false
  }, 500)
}

const renderChart = () => {
  const container = document.getElementById('wordcloud-chart')
  if (!container) return
  
  if (chart) {
    chart.dispose()
  }
  
  chart = echarts.init(container)
  
  const option = {
    tooltip: {
      show: true,
      formatter: (params) => `${params.name}: ${params.value}次`
    },
    series: [{
      type: 'wordCloud',
      shape: 'circle',
      width: '100%',
      height: '100%',
      sizeRange: [14, 60],
      rotationRange: [-45, 45],
      rotationStep: 15,
      gridSize: 20,
      drawOutOfBound: false,
      textStyle: {
        fontFamily: 'sans-serif',
        fontWeight: 'normal',
        color: function () {
          return 'rgb(' + [
            Math.round(Math.random() * 160 + 40),
            Math.round(Math.random() * 160 + 40),
            Math.round(Math.random() * 160 + 40)
          ].join(',') + ')'
        }
      },
      emphasis: {
        textStyle: {
          fontWeight: 'bold',
          color: '#007acc'
        }
      },
      data: mockWordData
    }]
  }
  
  chart.setOption(option)
  
  window.addEventListener('resize', () => {
    chart && chart.resize()
  })
}

onMounted(() => {
  nextTick(() => {
    renderChart()
  })
})

onUnmounted(() => {
  if (chart) {
    chart.dispose()
  }
})
</script>

<style scoped>
.wordcloud-container {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: bold;
}

.chart-container {
  margin-top: 20px;
  min-height: 550px;
}

.loading-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #999;
}

.loading-tip .el-icon {
  font-size: 40px;
  margin-bottom: 16px;
}
</style>