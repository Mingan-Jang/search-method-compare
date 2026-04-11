<template>
  <el-container class="layout-container">
    <el-header>
      <h2>🔍 Search Methodology Comparison Lab</h2>
    </el-header>

    <el-main>
      <el-row :gutter="20">
        <el-col :span="18">
          <el-input
            v-model="searchKey"
            placeholder="輸入關鍵字進行實驗..."
            clearable
          />
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="handleSearch"
            >執行比對搜尋</el-button
          >
        </el-col>
      </el-row>

      <el-tabs
        v-model="activeMethod"
        class="demo-tabs"
        style="margin-top: 20px"
      >
        <el-tab-pane label="Elasticsearch (Service)" name="es">
          <el-card>後端 ES 檢索結果與效能分析...</el-card>
        </el-tab-pane>
        <el-tab-pane label="Postgres (DB)" name="pg">
          <el-card>後端 PG 全文檢索結果與效能分析...</el-card>
        </el-tab-pane>
        <el-tab-pane label="WASM (Client)" name="wasm">
          <el-card>前端 WebAssembly 檢索結果與效能分析...</el-card>
        </el-tab-pane>
      </el-tabs>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref } from "vue";

const searchKey = ref("");
const activeMethod = ref("es");

const handleSearch = () => {
  console.log(`正在使用 ${activeMethod.value} 模式搜尋: ${searchKey.value}`);
};
</script>

<style scoped>
.layout-container {
  max-width: 1200px;
  margin: 0 auto;
}
h2 {
  color: #409eff;
  text-align: center;
}
</style>
