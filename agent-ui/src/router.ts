import { createRouter, createWebHistory } from "vue-router";

import ToolsView from "./views/ToolsView.vue";
import ToolCreateView from "./views/ToolCreateView.vue";
import AgentsView from "./views/AgentsView.vue";
import ChatsView from "./views/ChatsView.vue";
import AgentsCreateView from "./views/AgentsCreateView.vue";

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/tools" },
    { path: "/tools", component: ToolsView },
    { path: "/tools/new", component: ToolCreateView },
    { path: "/agents", component: AgentsView },
    { path: "/agents/new", component: AgentsCreateView },
    { path: "/chats", component: ChatsView },
  ],
});
