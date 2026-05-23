<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <div class="logo-icon">
          <el-icon :size="48" color="#007acc"><UserFilled /></el-icon>
        </div>
        <h2>创建新账号</h2>
        <p>加入电力设备故障知识库系统</p>
      </div>

      <el-form :model="regForm" class="login-form" @submit.prevent="handleRegister">
        <el-form-item>
          <el-input
            v-model="regForm.username"
            placeholder="设置用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item>
          <el-input
            v-model="regForm.password"
            type="password"
            placeholder="设置密码"
            prefix-icon="Lock"
            show-password
            size="large"
          />
        </el-form-item>

        <el-form-item>
          <el-input
            v-model="regForm.confirmPwd"
            type="password"
            placeholder="确认密码"
            prefix-icon="CircleCheck"
            show-password
            size="large"
          />
        </el-form-item>

        <!-- 直接展示三个角色，不带label -->
        <div class="role-group">
          <el-radio-group v-model="regForm.role">
            <el-radio label="admin">管理员</el-radio>
            <el-radio label="expert">技术专家</el-radio>
            <el-radio label="user">普通用户</el-radio>
          </el-radio-group>
        </div>

        <el-button
          type="primary"
          class="login-btn"
          size="large"
          @click="handleRegister"
          :loading="loading"
        >
          注 册
        </el-button>

        <div class="login-footer">
          <span>已有账号？</span>
          <el-link type="primary" @click="router.push('/login')">立即登录</el-link>
        </div>
      </el-form>
    </div>

    <div class="login-footer-decoration">
      <span>电力设备故障知识库系统 © 2026</span>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UserFilled } from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()
const loading = ref(false)

const regForm = reactive({
  username: '',
  password: '',
  confirmPwd: '',
  role: 'user'
})

const handleRegister = async () => {
  const username = regForm.username.trim()
  const password = regForm.password
  const confirmPwd = regForm.confirmPwd
  const role = regForm.role

  if (!username || !password || !confirmPwd) {
    ElMessage.warning('请填写完整信息')
    return
  }

  if (password !== confirmPwd) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }

  if (!['admin', 'expert', 'user'].includes(role)) {
    ElMessage.warning('请选择正确的角色类型')
    return
  }

  loading.value = true
  try {
    const response = await axios.post('http://127.0.0.1:5002/api/register', {
      username,
      password,
      role
    })

    if (response.data.code === 200) {
      ElMessage.success('注册成功，请登录')
      router.push('/login')
    } else {
      ElMessage.error(response.data.message || '注册失败')
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('网络错误或服务器未启动')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
}

.login-container::before {
  content: '';
  position: absolute;
  width: 300px;
  height: 300px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  top: -150px;
  right: -150px;
}

.login-container::after {
  content: '';
  position: absolute;
  width: 500px;
  height: 500px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 50%;
  bottom: -250px;
  left: -250px;
}

.login-box {
  width: 420px;
  padding: 48px 40px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 24px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  z-index: 1;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.login-box:hover {
  transform: translateY(-5px);
  box-shadow: 0 25px 70px rgba(0, 0, 0, 0.35);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  margin-bottom: 16px;
}

.login-header h2 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 600;
  background: linear-gradient(135deg, #007acc, #00b4d8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-header p {
  color: #888;
  font-size: 14px;
  margin: 0;
  letter-spacing: 1px;
}

.login-form {
  margin-top: 8px;
}

.login-form :deep(.el-input__wrapper) {
  border-radius: 12px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 12px rgba(0, 122, 204, 0.15);
  border-color: #007acc;
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(0, 122, 204, 0.2);
  border-color: #007acc;
}

.role-group {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin: 24px 0 16px;
  flex-wrap: wrap;
}

.role-group :deep(.el-radio__label) {
  font-size: 14px;
}

.login-btn {
  width: 100%;
  height: 44px;
  background: linear-gradient(135deg, #007acc, #00b4d8);
  border: none;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 2px;
  border-radius: 12px;
  margin-top: 8px;
  transition: all 0.3s ease;
}

.login-btn:hover {
  background: linear-gradient(135deg, #005a8c, #0096b0);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 122, 204, 0.3);
}

.login-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 14px;
  color: #888;
}

.login-footer :deep(.el-link) {
  font-size: 14px;
  margin-left: 4px;
}

.login-footer-decoration {
  position: absolute;
  bottom: 20px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  z-index: 1;
}

@media (max-width: 480px) {
  .login-box {
    width: 90%;
    padding: 32px 24px;
    margin: 0 16px;
  }

  .login-header h2 {
    font-size: 20px;
  }
}
</style>