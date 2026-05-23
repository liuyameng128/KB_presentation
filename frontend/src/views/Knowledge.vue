<template>
  <div class="container">
    <el-card shadow="never">
      <template #header>
        <div class="flex-between">
          <b style="font-size: 1.2rem">⚡ 电力故障知识库管理</b>
          <div>
            <el-button type="success" @click="openUploadDialog">
              <el-icon><Upload /></el-icon> 上传文件
            </el-button>
            <el-button type="primary" @click="openAddDialog">
              <el-icon><Plus /></el-icon> 添加新的知识
            </el-button>
          </div>
        </div>
      </template>

      <!-- 双搜索栏 -->
      <div class="search-bar">
        <el-input 
          v-model="searchEquipment" 
          placeholder="设备名称" 
          style="width: 250px"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-input 
          v-model="searchPhenomenon" 
          placeholder="故障现象" 
          style="width: 300px"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="resetSearch">重置</el-button>
      </div>

      <!-- 批量操作栏 -->
      <div class="batch-actions" v-if="selectedRows.length > 0">
        <el-button type="danger" @click="batchDelete">
          <el-icon><Delete /></el-icon> 批量删除 ({{ selectedRows.length }})
        </el-button>
        <span class="selected-info">已选择 {{ selectedRows.length }} 条记录</span>
      </div>

      <!-- 数据表格 -->
      <el-table 
        :data="knowledgeList" 
        v-loading="loading" 
        border stripe 
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="equipment" label="设备名称" width="200" show-overflow-tooltip />
        <el-table-column prop="phenomenon" label="故障现象" show-overflow-tooltip />
        <el-table-column prop="file_name" label="来源文件" width="180" show-overflow-tooltip />
        <el-table-column prop="create_time" label="创建时间" width="160" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="handleDetail(scope.row)">详情</el-button>
            <el-button link type="warning" @click="openEditDialog(scope.row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页组件 -->
      <div class="pagination-container">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100, 200]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog 
      v-model="detailVisible" 
      title="故障知识详情" 
      width="70%"
      @close="detailVisible = false"
    >
      <el-descriptions :column="1" border>
        <el-descriptions-item label="设备名称">{{ activeRow.equipment }}</el-descriptions-item>
        <el-descriptions-item label="故障现象">{{ activeRow.phenomenon }}</el-descriptions-item>
        <el-descriptions-item label="故障原因">
          <el-tag v-for="c in formatArray(activeRow.causes)" :key="c" style="margin-right:5px; margin-bottom:5px">
            {{ c }}
          </el-tag>
          <span v-if="formatArray(activeRow.causes).length === 0" style="color: #999">无</span>
        </el-descriptions-item>
        <el-descriptions-item label="处理措施">
          <div v-for="(s, i) in formatArray(activeRow.solutions)" :key="i" style="margin-bottom: 8px">
            {{ i+1 }}. {{ s }}
          </div>
          <span v-if="formatArray(activeRow.solutions).length === 0" style="color: #999">无</span>
        </el-descriptions-item>
        <el-descriptions-item label="关键词">
          <el-tag type="info" v-for="kw in formatArray(activeRow.keywords)" :key="kw" style="margin-right:5px; margin-bottom:5px">
            {{ kw }}
          </el-tag>
          <span v-if="formatArray(activeRow.keywords).length === 0" style="color: #999">无</span>
        </el-descriptions-item>
        <el-descriptions-item label="章节">{{ activeRow.chapter || '无' }}</el-descriptions-item>
        <el-descriptions-item label="来源文件">{{ activeRow.file_name || '未知' }}</el-descriptions-item>
        <el-descriptions-item label="原文">
          <pre class="source-pre">{{ activeRow.source_text || '无' }}</pre>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 添加/编辑弹窗 -->
    <el-dialog 
      v-model="formDialogVisible" 
      :title="formTitle" 
      width="60%"
      @close="handleDialogClose"
    >
      <el-form :model="formData" label-width="100px">
        <el-form-item label="设备名称" required>
          <el-input v-model="formData.equipment" placeholder="请输入设备名称" />
        </el-form-item>
        <el-form-item label="故障现象" required>
          <el-input v-model="formData.phenomenon" type="textarea" :rows="3" placeholder="请输入故障现象" />
        </el-form-item>
        <el-form-item label="故障原因">
          <div class="input-with-add">
            <el-input 
              v-model="causeInput" 
              placeholder="输入原因后按回车添加"
              @keyup.enter="addCause"
            />
            <el-button @click="addCause" size="small">添加</el-button>
          </div>
          <div class="tag-list">
            <el-tag 
              v-for="(c, idx) in formData.causes" 
              :key="idx" 
              closable 
              @close="removeCause(idx)"
              style="margin: 5px"
            >
              {{ c }}
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item label="处理措施">
          <div class="input-with-add">
            <el-input 
              v-model="solutionInput" 
              placeholder="输入措施后按回车添加"
              @keyup.enter="addSolution"
            />
            <el-button @click="addSolution" size="small">添加</el-button>
          </div>
          <div class="tag-list">
            <el-tag 
              v-for="(s, idx) in formData.solutions" 
              :key="idx" 
              closable 
              @close="removeSolution(idx)"
              style="margin: 5px"
            >
              {{ s }}
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item label="关键词">
          <div class="input-with-add">
            <el-input 
              v-model="keywordInput" 
              placeholder="输入关键词后按回车添加"
              @keyup.enter="addKeyword"
            />
            <el-button @click="addKeyword" size="small">添加</el-button>
          </div>
          <div class="tag-list">
            <el-tag 
              type="info"
              v-for="(kw, idx) in formData.keywords" 
              :key="idx" 
              closable 
              @close="removeKeyword(idx)"
              style="margin: 5px"
            >
              {{ kw }}
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item label="原文">
          <el-input v-model="formData.source_text" type="textarea" :rows="6" placeholder="请输入原文内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" @click="saveKnowledge" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 上传文件弹窗 -->
    <el-dialog 
      v-model="uploadDialog" 
      title="上传文件并提取知识" 
      width="500px"
      @close="handleUploadDialogClose"
    >
      <el-upload
        class="upload-demo"
        drag
        :action="uploadUrl"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
        :headers="uploadHeaders"
        :disabled="uploading"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 .pdf, .md, .txt, .doc, .docx 格式文件，文件大小不超过 50MB
          </div>
        </template>
      </el-upload>
      <div v-if="uploading" class="upload-progress">
        <el-progress :percentage="uploadProgress" :stroke-width="8" />
        <p>正在处理文件，请稍候...</p>
      </div>
      <template #footer>
        <el-button @click="closeUploadDialog">取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Upload, Search, Delete, UploadFilled } from '@element-plus/icons-vue';
import axios from 'axios';

const API_BASE = 'http://127.0.0.1:5002/api/knowledge';

const knowledgeList = ref([]);
const loading = ref(false);
const saving = ref(false);
const searchEquipment = ref('');      // 设备名称搜索关键字
const searchPhenomenon = ref('');     // 故障现象搜索关键字
const selectedRows = ref([]);
const uploading = ref(false);
const uploadProgress = ref(0);

// 分页变量
const currentPage = ref(1);
const pageSize = ref(50);
const total = ref(0);

// 详情弹窗
const detailVisible = ref(false);
const activeRow = ref({});

// 添加/编辑弹窗
const formDialogVisible = ref(false);
const formTitle = ref('添加知识');
const isEdit = ref(false);
const formData = reactive({
  id: null,
  equipment: '',
  phenomenon: '',
  causes: [],
  solutions: [],
  keywords: [],
  source_text: ''
});

// 临时输入
const causeInput = ref('');
const solutionInput = ref('');
const keywordInput = ref('');

// 上传弹窗
const uploadDialog = ref(false);
const uploadUrl = `${API_BASE}/upload_file`;
const uploadHeaders = { 'Content-Type': 'multipart/form-data' };

// 获取数据（支持分页和双条件搜索）
const fetchData = async () => {
  loading.value = true;
  try {
    const res = await axios.get(`${API_BASE}/list`, {
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
        equipment: searchEquipment.value,
        phenomenon: searchPhenomenon.value
      }
    });
    if (res.data.code === 200) {
      knowledgeList.value = res.data.data;
      total.value = res.data.total;
    } else {
      ElMessage.error(res.data.msg || '获取数据失败');
    }
  } catch (err) {
    console.error('获取数据失败', err);
    ElMessage.error('获取数据失败，请检查后端服务');
  } finally {
    loading.value = false;
  }
};

// 搜索（重置到第一页）
const handleSearch = () => {
  currentPage.value = 1;
  fetchData();
};

// 重置搜索
const resetSearch = () => {
  searchEquipment.value = '';
  searchPhenomenon.value = '';
  currentPage.value = 1;
  fetchData();
};

// 分页事件
const handleSizeChange = (val) => {
  pageSize.value = val;
  currentPage.value = 1;
  fetchData();
};

const handleCurrentChange = (val) => {
  currentPage.value = val;
  fetchData();
};

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedRows.value = selection;
};

// 详情
const handleDetail = (row) => {
  activeRow.value = row;
  detailVisible.value = true;
};

// 打开添加弹窗
const openAddDialog = () => {
  isEdit.value = false;
  formTitle.value = '添加知识';
  resetForm();
  formDialogVisible.value = true;
};

// 打开编辑弹窗
const openEditDialog = (row) => {
  isEdit.value = true;
  formTitle.value = '编辑知识';
  formData.id = row.id;
  formData.equipment = row.equipment || '';
  formData.phenomenon = row.phenomenon || '';
  formData.causes = formatArray(row.causes);
  formData.solutions = formatArray(row.solutions);
  formData.keywords = formatArray(row.keywords);
  formData.source_text = row.source_text || '';
  formDialogVisible.value = true;
};

// 重置表单
const resetForm = () => {
  formData.id = null;
  formData.equipment = '';
  formData.phenomenon = '';
  formData.causes = [];
  formData.solutions = [];
  formData.keywords = [];
  formData.source_text = '';
  causeInput.value = '';
  solutionInput.value = '';
  keywordInput.value = '';
};

// 关闭弹窗
const closeDialog = () => {
  formDialogVisible.value = false;
  resetForm();
};

// 弹窗关闭时的回调
const handleDialogClose = () => {
  resetForm();
};

// 添加原因
const addCause = () => {
  if (causeInput.value.trim()) {
    formData.causes.push(causeInput.value.trim());
    causeInput.value = '';
  }
};

const removeCause = (idx) => {
  formData.causes.splice(idx, 1);
};

// 添加措施
const addSolution = () => {
  if (solutionInput.value.trim()) {
    formData.solutions.push(solutionInput.value.trim());
    solutionInput.value = '';
  }
};

const removeSolution = (idx) => {
  formData.solutions.splice(idx, 1);
};

// 添加关键词
const addKeyword = () => {
  if (keywordInput.value.trim()) {
    formData.keywords.push(keywordInput.value.trim());
    keywordInput.value = '';
  }
};

const removeKeyword = (idx) => {
  formData.keywords.splice(idx, 1);
};

// 保存知识
const saveKnowledge = async () => {
  if (!formData.equipment || !formData.phenomenon) {
    ElMessage.warning('请填写设备名称和故障现象');
    return;
  }
  
  saving.value = true;
  try {
    let res;
    if (isEdit.value) {
      res = await axios.put(`${API_BASE}/update/${formData.id}`, formData);
    } else {
      res = await axios.post(`${API_BASE}/add`, formData);
    }
    
    if (res.data.code === 200) {
      ElMessage.success(res.data.msg);
      closeDialog();
      fetchData();
    } else {
      ElMessage.error(res.data.msg || '保存失败');
    }
  } catch (err) {
    console.error('保存失败', err);
    ElMessage.error('保存失败');
  } finally {
    saving.value = false;
  }
};

// 删除单条知识
const handleDelete = async (row) => {
  ElMessageBox.confirm(`确定要删除设备"${row.equipment}"的知识吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await axios.delete(`${API_BASE}/delete/${row.id}`);
      if (res.data.code === 200) {
        ElMessage.success('删除成功');
        fetchData();
      } else {
        ElMessage.error(res.data.msg || '删除失败');
      }
    } catch (err) {
      console.error('删除失败', err);
      ElMessage.error('删除失败');
    }
  }).catch(() => {});
};

// 批量删除
const batchDelete = async () => {
  const ids = selectedRows.value.map(row => row.id);
  ElMessageBox.confirm(`确定要删除选中的 ${ids.length} 条知识吗？此操作不可恢复！`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await axios.post(`${API_BASE}/batch_delete`, { ids });
      if (res.data.code === 200) {
        ElMessage.success(res.data.msg);
        fetchData();
        selectedRows.value = [];
      } else {
        ElMessage.error(res.data.msg || '删除失败');
      }
    } catch (err) {
      console.error('批量删除失败', err);
      ElMessage.error('批量删除失败');
    }
  }).catch(() => {});
};

// 打开上传弹窗
const openUploadDialog = () => {
  uploadDialog.value = true;
  uploading.value = false;
  uploadProgress.value = 0;
};

// 关闭上传弹窗
const closeUploadDialog = () => {
  uploadDialog.value = false;
  uploading.value = false;
  uploadProgress.value = 0;
};

// 上传弹窗关闭回调
const handleUploadDialogClose = () => {
  uploading.value = false;
  uploadProgress.value = 0;
};

// 上传前验证
const beforeUpload = (file) => {
  const allowedTypes = ['.pdf', '.md', '.txt', '.doc', '.docx'];
  const fileExt = '.' + file.name.split('.').pop().toLowerCase();
  if (!allowedTypes.includes(fileExt)) {
    ElMessage.error(`不支持的文件类型: ${fileExt}`);
    return false;
  }
  
  const maxSize = 50 * 1024 * 1024;
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 50MB');
    return false;
  }
  
  uploading.value = true;
  uploadProgress.value = 0;
  
  const interval = setInterval(() => {
    if (uploadProgress.value < 90) {
      uploadProgress.value += 10;
    }
  }, 500);
  
  window._uploadInterval = interval;
  
  return true;
};

// 上传成功
const handleUploadSuccess = (response) => {
  if (window._uploadInterval) {
    clearInterval(window._uploadInterval);
  }
  uploadProgress.value = 100;
  
  if (response.code === 200) {
    ElMessage.success(response.msg);
    setTimeout(() => {
      closeUploadDialog();
      fetchData();
    }, 500);
  } else {
    ElMessage.error(response.msg || '上传处理失败');
    uploading.value = false;
    uploadProgress.value = 0;
  }
};

// 上传失败
const handleUploadError = (error) => {
  if (window._uploadInterval) {
    clearInterval(window._uploadInterval);
  }
  console.error('上传失败', error);
  ElMessage.error('文件上传失败，请检查后端服务');
  uploading.value = false;
  uploadProgress.value = 0;
};

// 格式化数组（处理 JSON 字符串或数组）
const formatArray = (data) => {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  try {
    const parsed = JSON.parse(data);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

onMounted(() => {
  fetchData();
});
</script>

<style scoped>
.container { 
  padding: 20px; 
  background: #f5f7fa;
  min-height: 100vh;
}

.flex-between { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
}

/* 搜索栏 */
.search-bar {
  margin: 20px 0;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

/* 批量操作栏 */
.batch-actions {
  margin: 15px 0;
  padding: 12px 15px;
  background: #ecf5ff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 15px;
}

.selected-info {
  color: #007acc;
  font-size: 14px;
}

/* 分页 */
.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 弹窗表单 */
.input-with-add {
  display: flex;
  gap: 10px;
  width: 100%;
}

.input-with-add .el-input {
  flex: 1;
}

.tag-list {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
}

/* 原文预览 */
.source-pre { 
  background: #f4f4f4; 
  padding: 12px; 
  white-space: pre-wrap; 
  font-size: 12px; 
  max-height: 400px; 
  overflow-y: auto; 
  font-family: 'Courier New', monospace;
  border-radius: 6px;
}

/* 上传区域 */
.upload-demo {
  width: 100%;
}

.upload-progress {
  margin-top: 20px;
  text-align: center;
}

.upload-progress p {
  margin-top: 10px;
  color: #666;
  font-size: 13px;
}

:deep(.el-upload-dragger) {
  width: 100%;
  padding: 40px;
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-link) {
  margin: 0 4px;
}
</style>