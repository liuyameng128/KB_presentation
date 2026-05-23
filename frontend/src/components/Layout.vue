<template>
  <div class="layout-container">
    <div class="sidebar" :class="{ collapsed: isCollapsed }">
      <div class="logo" @click="goHome">
        <el-icon :size="28" color="#007acc"><Cpu /></el-icon>
        <span v-if="!isCollapsed">电力设备故障知识库</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapsed"
        :collapse-transition="false"
        router
      >
        <el-menu-item
          index="/knowledge"
          v-if="userRole === 'admin' || userRole === 'expert'"
          @click="navigateTo('/knowledge')"
        >
          <el-icon><Document /></el-icon>
          <template #title>知识管理界面</template>
        </el-menu-item>

        <el-menu-item
          index="/statistics"
          v-if="userRole === 'admin'"
          @click="navigateTo('/statistics')"
        >
          <el-icon><PieChart /></el-icon>
          <template #title>统计分析</template>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <el-tooltip :content="isCollapsed ? '展开' : '收起'" placement="right">
          <el-button :icon="isCollapsed ? Expand : Fold" @click="toggleCollapse" text />
        </el-tooltip>
        <el-tooltip content="退出登录" placement="right">
          <el-button :icon="SwitchButton" @click="handleLogout" text style="color: #f56c6c" />
        </el-tooltip>
      </div>
    </div>

    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Cpu,
  Document,
  PieChart,
  Fold,
  Expand,
  SwitchButton
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const isCollapsed = ref(false)
const userRole = ref('admin')

const activeMenu = computed(() => route.path)

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

const goHome = () => {
  if (userRole.value === 'admin') {
    router.push('/knowledge')
  } else if (userRole.value === 'expert') {
    router.push('/knowledge')
  } else {
    router.push('/knowledge')
  }
}

const navigateTo = (path) => {
  router.push(path)
}

const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(() => {
      localStorage.clear()
      sessionStorage.clear()
      ElMessage.success('已退出登录')
      router.push('/login')
    })
    .catch(() => {})
}

onMounted(() => {
  userRole.value = localStorage.getItem('userRole') || 'admin'
})
</script>

<style scoped>
.layout-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 240px;
  background: #1e1e2f;
  color: #fff;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.sidebar.collapsed {
  width: 64px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 16px;
  font-size: 18px;
  font-weight: bold;
  color: #fff;
  cursor: pointer;
  border-bottom: 1px solid #2c2c3a;
  transition: all 0.3s ease;
  white-space: nowrap;
  overflow: hidden;
}

.logo:hover {
  background: #2c2c3a;
}

:deep(.el-menu) {
  flex: 1;
  border-right: none;
  background: #1e1e2f;
}

:deep(.el-menu-item) {
  color: #b0b0c0;
  height: 48px;
  line-height: 48px;
}

:deep(.el-menu-item.is-active) {
  color: #007acc;
  background: #2c2c3a;
}

:deep(.el-menu-item:hover) {
  background: #2c2c3a;
  color: #fff;
}

:deep(.el-menu-item .el-icon) {
  font-size: 20px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #2c2c3a;
  display: flex;
  justify-content: space-around;
  gap: 12px;
}

.sidebar-footer .el-button {
  color: #b0b0c0;
  font-size: 20px;
  padding: 8px;
}

.sidebar-footer .el-button:hover {
  color: #007acc;
  background: #2c2c3a;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  background: #f5f7fa;
}

.main-content::-webkit-scrollbar {
  width: 8px;
}

.main-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.main-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.main-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>