<template>
  <div class="d-flex vh-100">
    <aside class="sidebar bg-dark text-white p-3">
      <h5 class="mb-4">Octobox</h5>

      <ul class="nav flex-column gap-2">
        <li class="nav-item">
          <Button
            :as="RouterLink"
            v-bind="{ to: '/tools' }"
            variant="ghost"
            :class="navLinkClass('/tools')"
            block
          >
            <template #icon-left><Icon name="tools" /></template>
            Tools
          </Button>
        </li>

        <li class="nav-item">
          <Button
            :as="RouterLink"
            v-bind="{ to: '/agents' }"
            variant="ghost"
            :class="navLinkClass('/agents')"
            block
          >
            <template #icon-left><Icon name="robot" /></template>
            Agents
          </Button>
        </li>

        <li class="nav-item">
          <Button
            :as="RouterLink"
            v-bind="{ to: '/chats' }"
            variant="ghost"
            :class="navLinkClass('/chats')"
            block
          >
            <template #icon-left><Icon name="chat-dots" /></template>
            Chats
          </Button>
        </li>
      </ul>
    </aside>

    <main class="flex-fill p-4 overflow-auto bg-light">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, useRoute } from "vue-router";
import { Button, Icon } from "@/components/atoms";

const route = useRoute();

function navLinkClass(path: string) {
  const isActive = route.path === path || route.path.startsWith(path + "/");
  return [
    "nav-link-btn",
    { "active-btn": isActive },
  ];
}
</script>

<style scoped>
.sidebar {
  width: 240px;
}

/* Visual treatment for sidebar links */
.nav-link-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;

  justify-content: flex-start;
  text-align: left;

  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;

  color: #adb5bd;
}

.nav-link-btn:hover {
  background-color: #2c3034;
  color: #fff;
}

.active-btn {
  background-color: #0d6efd;
  color: #fff;
}
</style>
