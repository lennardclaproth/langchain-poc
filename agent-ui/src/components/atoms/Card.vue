<template lang="">
    <div class="card">
        <div class="card-body">
            <slot>

            </slot>
        </div>
    </div>
</template>
<script>
export default {
    
}
</script>
<style scoped>
.card {
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    overflow: hidden;
    padding: 0;
}

.card-body {
    padding: 36px;
}
</style>