import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // 新增：引入路由

import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.use(router) // 新增：必须使用 router 插件
app.mount('#app')