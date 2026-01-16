---
id: FIX-0008
uid: afa8e7
type: fix
status: closed
stage: done
title: 启用孤儿问题的创建
created_at: '2026-01-14T16:57:42'
opened_at: '2026-01-14T16:57:42'
updated_at: '2026-01-14T16:57:47'
closed_at: '2026-01-14T16:57:47'
parent: FEAT-0063
solution: implemented
dependencies: []
related: []
tags: []
---

## FIX-0008: 启用孤儿问题的创建

## 目标

确保即使问题是"孤儿"（即没有父史诗）时也能创建问题。

## 验收标准

- [x] 孤儿问题可以成功创建而不出现错误。

## 技术任务

- [x] 允许在问题创建期间`parent`为空。

## Review Comments

- [x] Self review
