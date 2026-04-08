# Smart Personal Website — 架构与实现指南

本文档描述如何将个人网站升级为「可学习用户行为并做个性化推荐」的全栈系统，涵盖 Backend、Data Pipeline、ML Recommendation 与部署。适合作为简历/作品集上的 **ML System Design Project** 说明。

---

## 1. 系统总览

```
Frontend (当前: HTML/CSS/JS → 可选升级 React)
        │
        │ REST API (或继续 Firebase 直连)
        ▼
Backend Server (Node.js / Python FastAPI)
        │
        ├── MongoDB (用户行为 + 内容元数据)
        └── ML Recommendation Engine (离线训练 + 在线推理)
```

**四层结构**：Frontend UI → Backend API → Database + Data Pipeline → ML Engine。

---

## 2. 数据模型（MongoDB）

### 2.1 用户行为 `UserInteraction`

```javascript
{
  _id: ObjectId,
  user_id: String,      // 匿名 id (localStorage) 或 Firebase UID
  page_id: String,      // 如 "projects", "coursework"
  event_type: String,   // "page_view" | "click" | "scroll" | "dwell"
  timestamp: ISODate,
  dwell_time: Number,   // 秒，可选
  scroll_depth: Number, // 0–100，可选
  metadata: Object      // 如 button_id, link_href
}
```

**索引建议**：`(user_id, timestamp)`、`(page_id, timestamp)`、`(event_type, timestamp)`，便于按用户或按内容做聚合与特征。

### 2.2 内容元数据 `Content`

```javascript
{
  _id: String,          // 与 page_id 一致，如 "projects"
  title: String,
  tags: [String],       // ["ml", "systems", "embedded"]
  category: String,     // "projects" | "academic" | "tools"
  popularity: Number,    // 可选：点击/浏览计数，用于热门推荐
  updated_at: ISODate
}
```

---

## 3. Backend API 设计（REST）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/interactions` | 上报一条行为（body: user_id, page_id, event_type, timestamp, dwell_time?） |
| GET  | `/api/recommendations?user_id=xxx&limit=5` | 返回个性化推荐内容列表 |
| GET  | `/api/content` | 返回所有内容元数据（供前端做 fallback 或预加载） |

**认证**：  
- 上报行为可用 API Key 或无需登录（仅限 rate limit）。  
- 若启用 Firebase Auth，可在后端用 Admin SDK 校验 `idToken`，将 `user_id` 与 Firebase UID 绑定。

---

## 4. ML 推荐引擎

### 4.1 Option A：Logistic Regression（点击率预估）

**目标**：预测 `P(click | user, content)`。

**特征示例**：
- 用户侧：历史点击的 tags/category 的 one-hot 或 embedding 聚合、平均 dwell_time、访问频次。
- 内容侧：content 的 tags、category、popularity。
- 交叉：当前内容 tag 与用户历史偏好 tag 的重叠度。

**流程**：
1. **离线**：从 MongoDB 聚合 `(user_id, content_id, label=click/not)`，做特征工程，用 sklearn 或 XGBoost 训练 LR/GBDT。
2. **在线**：用户请求推荐时，对候选 content 算特征，模型推理得到分数，按分数排序取 top‑k。
3. 模型可定期（如每日）用新数据重训，导出成 pickle/ONNX 供 backend 加载。

### 4.2 Option B：Collaborative Filtering（用户–内容矩阵）

**思路**：`users × content` 矩阵（值为点击/浏览强度），用矩阵分解（SVD、ALS）或 KNN（找相似用户）得到「用户–内容」得分。

**流程**：
1. **离线**：从 MongoDB 建 user–content 矩阵（可加时间衰减），训练 SVD/ALS 或算 item–item / user–user 相似度。
2. **在线**：给定 user_id，取该用户向量与所有 content 向量内积（或 KNN 聚合），排序取 top‑k。

### 4.3 冷启动与 Fallback

- **新用户 / 无行为**：按 `popularity` 或随机推荐。
- **数据少**：规则推荐（同 category、同 tag）或 A/B 测试规则 vs 模型。

---

## 5. 实时推荐流程

```
用户浏览/点击
    → 前端 POST /api/interactions
    → Backend 写入 MongoDB（可异步）
    → 用户打开新页面或「推荐」入口
    → 前端 GET /api/recommendations?user_id=xxx
    → Backend 读 MongoDB，做特征 + 模型推理（或查预计算缓存）
    → 返回 [{ content_id, title, url }]
    → 前端渲染「Recommended for you」/「You may also like」
```

为降低延迟，可对「当前用户」的推荐结果做短时缓存（如 1–5 分钟）。

---

## 6. Firebase Auth 集成

1. 前端：用 Firebase Auth（Email/Google/GitHub）登录，拿 `idToken`。
2. 前端上报行为时带上 `idToken`（或后端用 cookie/session 关联已登录用户）。
3. Backend：用 Firebase Admin SDK 校验 `idToken`，得到 `uid`，将 `user_id` 与 `uid` 统一（便于登录用户做个性化与跨设备）。
4. 评论/留言/收藏可存 MongoDB，并带 `user_id`（Firebase UID）。

---

## 7. 性能与部署

- **API 缓存**：推荐结果按 user 缓存；内容列表可 CDN 或内存缓存。
- **数据库**：MongoDB 索引见上；读写分离或只读副本做推荐查询。
- **前端**：静态资源 CDN；懒加载、按需加载推荐模块。
- **部署示例**：
  - Frontend：Vercel / Netlify / GitHub Pages（当前方式）。
  - Backend：Railway / Render / Fly.io / Cloud Run。
  - DB：MongoDB Atlas。
  - Auth：已有 Firebase，保持不变。

---

## 8. 未来扩展

- **AI**：LLM 做文章摘要、语义搜索、站内问答机器人。
- **Analytics Dashboard**：行为统计、热门内容、推荐效果（CTR、停留时长）可视化。
- **A/B 测试**：规则推荐 vs ML 推荐，对比点击与停留指标。

---

## 9. 简历短版（Resume / Project Page）

可直接使用：

> **Smart Personal Website** (In Progress)  
> - Developing a full-stack personal website with MongoDB-backed REST APIs for user interaction logging.  
> - Building a lightweight recommendation system (logistic regression / collaborative filtering) for personalized content suggestions.  
> - Implementing real-time inference pipeline and dynamic UI recommendations.  
> - Integrating Firebase authentication and deploying on a custom domain.

此项目同时体现：**full-stack**、**data pipeline**、**ML system**、**system design**，适合 ML / Software / Systems 岗位的 portfolio 与面试讨论。
