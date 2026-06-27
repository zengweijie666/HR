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

    <!-- 收藏筛选 -->
    <el-select
      v-model="favoriteFilter"
      class="filter-bar__field filter-bar__field--fav"
      placeholder="收藏"
      clearable
      style="width: 120px"
      @change="handleSearch"
    >
      <el-option label="已收藏" :value="true" />
      <el-option label="未收藏" :value="false" />
    </el-select>

    <!-- 入库日期范围 -->
    <el-date-picker
      v-model="dateRange"
      class="filter-bar__field filter-bar__field--date"
      type="daterange"
      range-separator="至"
      start-placeholder="开始日期"
      end-placeholder="结束日期"
      value-format="YYYY-MM-DD"
      style="width: 260px"
      @change="handleSearch"
    />

    <!-- 排序字段 -->
    <el-select
      v-model="sortBy"
      class="filter-bar__field filter-bar__field--sort"
      style="width: 140px"
      @change="handleSearch"
    >
      <el-option label="入库时间" value="created_at" />
      <el-option label="工作经验" value="work_years" />
      <el-option label="学历" value="education_level" />
    </el-select>

    <!-- 排序方向 -->
    <el-select
      v-model="sortOrder"
      class="filter-bar__field filter-bar__field--order"
      style="width: 100px"
      @change="handleSearch"
    >
      <el-option label="降序" value="desc" />
      <el-option label="升序" value="asc" />
    </el-select>

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
  is_favorite?: boolean
  date_from?: string
  date_to?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

const emit = defineEmits<{
  /** 触发搜索 */
  (e: 'search', filters: ResumeFilters): void
  /** 触发重置（完全清空筛选） */
  (e: 'reset'): void
}>()

const keyword = ref<string>('')
const educationMin = ref<number | undefined>(undefined)
const workYearsMin = ref<number | undefined>(undefined)
const favoriteFilter = ref<boolean | undefined>(undefined)
const dateRange = ref<[string, string] | null>(null)
const sortBy = ref<string>('created_at')
const sortOrder = ref<'asc' | 'desc'>('desc')

/** 触发搜索事件 */
function handleSearch(): void {
  emit('search', {
    keyword: keyword.value || undefined,
    education_min: educationMin.value,
    work_years_min: workYearsMin.value,
    is_favorite: favoriteFilter.value,
    date_from: dateRange.value?.[0],
    date_to: dateRange.value?.[1],
    sort_by: sortBy.value,
    sort_order: sortOrder.value,
  })
}

/** 重置所有筛选条件 */
function handleReset(): void {
  keyword.value = ''
  educationMin.value = undefined
  workYearsMin.value = undefined
  favoriteFilter.value = undefined
  dateRange.value = null
  sortBy.value = 'created_at'
  sortOrder.value = 'desc'
  emit('reset')
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
