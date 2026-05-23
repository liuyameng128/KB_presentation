<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <el-icon :size="40" color="#007acc"><Cpu /></el-icon>
        <h2>电力故障知识库系统</h2>
        <p>Power Equipment Knowledge Base</p>
      </div>
      
      <el-form :model="loginForm" class="login-form" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input 
            v-model="loginForm.username" 
            placeholder="用户名" 
            prefix-icon="User" 
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="密码" 
            prefix-icon="Lock" 
            show-password 
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-button type="primary" class="login-btn" @click="handleLogin" :loading="loading">
          登 录
        </el-button>
        <div class="login-footer">
          <span>还没有账号？<el-link type="primary" @click="router.push('/register')">立即注册</el-link></span>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const loading = ref(false)
const loginForm = reactive({
  username: '',
  password: ''
})

// 检查是否已登录，如果已登录则直接跳转
onMounted(() => {
  const isLogin = localStorage.getItem('isLogin')
  const userRole = localStorage.getItem('userRole')
  
  if (isLogin === 'true' && userRole) {
    // 已登录，直接跳转到对应页面
    if (userRole === 'admin') {
      router.replace('/knowledge')
    } else {
      router.replace('/chat')
    }
  }
  
  // 清除可能存在的过期缓存
  const lastLoginTime = localStorage.getItem('lastLoginTime')
  if (lastLoginTime) {
    const daysPassed = (Date.now() - parseInt(lastLoginTime)) / (1000 * 60 * 60 * 24)
    if (daysPassed > 7) {
      // 超过7天，清除登录状态
      localStorage.removeItem('isLogin')
      localStorage.removeItem('userRole')
      localStorage.removeItem('username')
      localStorage.removeItem('lastLoginTime')
    }
  }
})

const handleLogin = async () => {
  // 前端验证
  if (!loginForm.username.trim()) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (!loginForm.password) {
    ElMessage.warning('请输入密码')
    return
  }
  
  loading.value = true
  try {
    const response = await axios.post('http://127.0.0.1:5002/api/login', {
      username: loginForm.username.trim(),
      password: loginForm.password
    })
    
    console.log('登录响应:', response.data)
    
    if (response.data.code === 200) {
      // 保存登录状态
      localStorage.setItem('isLogin', 'true')
      localStorage.setItem('userRole', response.data.role)
      localStorage.setItem('username', response.data.username || loginForm.username)
      localStorage.setItem('userId', response.data.user_id) 
      localStorage.setItem('lastLoginTime', Date.now().toString())
      
      ElMessage.success(`欢迎回来，${response.data.username || loginForm.username}`)
      
      // 根据角色跳转
      if (response.data.role === 'admin') {
        router.replace('/knowledge')
      } else {
        router.replace('/chat')
      }
    } else {
      ElMessage.error(response.data.message || '登录失败')
      // 登录失败时清除可能存在的旧状态
      localStorage.removeItem('isLogin')
      localStorage.removeItem('userRole')
    }
  } catch (error) {
    console.error('登录错误:', error)
    if (error.response) {
      ElMessage.error(error.response.data.message || '登录失败')
    } else if (error.request) {
      ElMessage.error('无法连接服务器，请检查后端服务是否启动')
    } else {
      ElMessage.error('登录失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #1e1e1e;
  background-image: radial-gradient(#333 1px, transparent 1px);
  background-size: 30px 30px;
}
.login-box {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.3);
}
.login-header { 
  text-align: center; 
  margin-bottom: 30px; 
}
.login-header h2 { 
  margin: 10px 0 5px; 
  color: #333; 
}
.login-header p { 
  color: #999; 
  font-size: 14px; 
  margin: 0; 
}
.login-form { 
  margin-top: 20px; 
}
.login-btn { 
  width: 100%; 
  height: 40px; 
  background-color: #007acc; 
  border: none; 
  font-size: 16px; 
  margin-top: 10px; 
}
.login-btn:hover {
  background-color: #005a8c;
}
.login-footer { 
  margin-top: 15px; 
  text-align: center; 
  font-size: 13px; 
  color: #666; 
}
</style>