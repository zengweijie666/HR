<!--
  文件名: components/resume/FilterBar.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 简历筛选栏
    - 关键词输入（带搜索图标）+ 学历下拉 + 工作年限 + 搜索/重置
    - 圆角输入框，响应式可换行
-->
<template>
  <div class="filter-bar">
    <el-input
      v-model="keyword"
      class="filter-bar__field filter-bar__field--keyword"
      placeholder="搜索姓名 / 技能 / 标签"
      clearable
      @keyup.enter="handleSearch"
    >
      <template #prefix>
        <el-icon class="filter-bar__search-icon"><Search /></el-icon>
      </template>
    </el-input>

    <el-select
      v-model="educationMin"
      class="filter-bar__field filter-bar__field--edu"
      placeholder="学历"
      clearable
    >
      <el-option
        v-for="(label, val) in EDUCATION_LEVELS"
        :key="val"
        :label="label"
        :value="Number(val)"
      />
    </el-select>

    <el-input-number
      v-model="workYearsMin"
      class="filter-bar__field filter-bar__field--years"
      :min="0"
      :max="50"
      controls-position="right"
      placeholder="最低年限"
    />

    <div class="filter-bar__actions">
      <el-button type="primary" class="filter-bar__search" @click="handleSearch">
        <el-icon class="filter-bar__btn-icon"><Search /></el-icon>
        搜索
      </el-button>
      <el-button text class="filter-bar__reset" @click="handleReset">重置</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * FilterBar 筛选栏
 * 收集关键词/学历/年限筛选条件并触发 search 事件
 */
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { EDUCATION_LEVELS } from '@/utils/constant'

/** 筛选条件结构 */
export interface ResumeFilters {
  keyword?: string
  education_min?: number
  work_years_min?: number
}

const emit = defineEmits<{
  /** 触发搜索 */
  (e: 'search', filters: ResumeFilters): void
}>()

const keyword = ref<string>('')
const educationMin = ref<number | undefined>(undefined)
const workYearsMin = ref<number | undefined>(undefined)

/** 触发搜索事件 */
function handleSearch(): void {
  emit('search', {
    keyword: keyword.value || undefined,
    education_min: educationMin.value,
    work_years_min: workYearsMin.value,
  })
}

/** 重置所有筛选条件 */
function handleReset(): void {
  keyword.value = ''
  educationMin.value = undefined
  workYearsMin.value = undefined
  emit('search', {})
}
</script>

<style scoped lang="scss">
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  background-color: var(--color-bg-card);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);

  &__field {
    :deep(.el-input__wrapper),
    :deep(.el-select__wrapper) {
      border-radius: var(--radius-md);
    }

    &--keyword {
      flex: 1 1 240px;
      min-width: 200px;
    }
    &--edu {
      width: 140px;
    }
    &--years {
      width: 140px;
    }
  }

  &__search-icon {
    color: var(--color-ink-mute);
  }

  &__actions {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    margin-left: auto;
  }

  &__search {
    transition: box-shadow var(--duration-fast) var(--ease-out);
    &:hover {
      box-shadow: var(--shadow-sm);
    }
  }

  &__btn-icon {
    margin-right: 4px;
  }
}
</style>
