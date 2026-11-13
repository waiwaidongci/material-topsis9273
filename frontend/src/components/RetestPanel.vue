<script setup lang="ts">
import {ref,computed,onMounted} from 'vue';
import {useResearch} from '../stores/research';
import {useAuth} from '../stores/auth';
import {useTask} from '../hooks/useTask';
import {metrics,retestConclusion} from '../constants/enums';
import {num,date,downloadRetest} from '../utils/format';
import ErrorNotice from './common/ErrorNotice.vue';
import type {Note,MetricCode,MetricStats} from '../types/domain';
const props=defineProps<{note:Note}>();
const research=useResearch(),auth=useAuth(),{error,busy,perform}=useTask();
const message=ref(''),batch=ref(''),lines=ref('');
const records=computed(()=>research.retests[props.note.id]||[]);
const versions=computed(()=>research.analyses[props.note.id]||[]);
const metricAliases:Record<string,MetricCode>={};
(Object.keys(metrics) as MetricCode[]).forEach(k=>{metricAliases[k]=k;metricAliases[metrics[k].name]=k;});
const metricName=(code:string)=>metrics[code as MetricCode]?.name||code;
const statText=(m:MetricStats)=>m.pairs?`${m.pairs}对配对 · 平均变化 ${num(m.mean_delta,4)} · 95%不确定范围 [${num(m.ci_low,4)}, ${num(m.ci_high,4)}]`:'0对配对';
onMounted(()=>perform(async()=>{await Promise.all([research.loadRetests(props.note.id),research.loadAnalyses(props.note.id)]);}));
function parseLines(){
 const rows:{sample_code:string;metric:MetricCode;value:number|null;unit:string}[]=[];
 const list=lines.value.split('\n');
 for(let i=0;i<list.length;i++){
  const line=list[i].trim();
  if(!line||line.startsWith('#'))continue;
  const parts=line.split(/[，,]/).map(s=>s.trim());
  if(parts.length!==4)return `第${i+1}行需要4个字段：编号,指标,数值,单位`;
  const metric=metricAliases[parts[1]];
  if(!metric)return `第${i+1}行指标“${parts[1]}”无法识别，可用 ${Object.keys(metrics).join('/')} 或中文名`;
  if(parts[2]==='')rows.push({sample_code:parts[0],metric,value:null,unit:parts[3]});
  else{const value=Number(parts[2]);if(!Number.isFinite(value))return `第${i+1}行数值“${parts[2]}”不是有限数`;rows.push({sample_code:parts[0],metric,value,unit:parts[3]});}
  if(!parts[3])return `第${i+1}行缺少单位`;
 }
 if(!rows.length)return '没有可提交的回传行';
 return rows;
}
async function send(){
 await perform(async()=>{
  const parsed=parseLines();
  if(typeof parsed==='string')throw new Error(parsed);
  const r=await research.submitRetests(props.note.id,{batch:batch.value,rows:parsed});
  message.value=`已接受${r.accepted}条`+(r.supplemented?`，补测入库${r.supplemented}条`:'')+(r.duplicates?`，重复投递${r.duplicates}条未重复计入`:'')+(r.conflicts.length?`，${r.conflicts.length}条与既有记录冲突未入库：${r.conflicts.map(c=>c.sample_code).join('、')}`:'')+'。';
  lines.value='';
 });
}
async function makeVersion(){
 await perform(async()=>{
  const a=await research.analyze(props.note.id);
  message.value=`已生成第${a.version}版配对分析，结论留档，旧版本仍可下载。`;
 });
}
</script>
<template>
<details class="edit-fold retest-fold">
<summary>湿热复测回传与配对分析 · {{records.length}}条回传 / {{versions.length}}版结论</summary>
<ErrorNotice :error="error"/>
<p v-if="message" class="success" role="status">{{message}}</p>
<form v-if="auth.canEdit" @submit.prevent="send">
<div class="two-col"><label>回传批次<input v-model="batch" maxLength="100" placeholder="例如 RH85-20261120"/></label></div>
<label>回传明细（每行：编号,指标,数值,单位；数值留空记为缺测）<textarea v-model="lines" rows="4" placeholder="LY01,absorption,0.71,αw&#10;LY07,吸声系数,,αw"/></label>
<div class="button-row"><button class="primary" :disabled="busy">提交回传</button><button type="button" :disabled="busy||!records.length" @click="makeVersion">生成配对分析版本 →</button></div>
</form>
<p v-else class="muted">观察员可阅读回传台账与各版分析结论。</p>
<details v-if="records.length" class="retest-ledger"><summary>回传台账 {{records.length}}条（重复投递不重复计入）</summary>
<div class="table-scroll"><table><thead><tr><th>记录</th><th>试件</th><th>指标</th><th>数值</th><th>单位</th><th>批次</th><th>回传人</th><th>时间</th></tr></thead><tbody><tr v-for="r in records" :key="r.id"><td>#{{r.id}}</td><td><b>{{r.sample_code}}</b></td><td>{{metricName(r.metric)}}</td><td>{{r.value===null?'缺测':num(r.value,4)}}</td><td>{{r.unit}}</td><td>{{r.batch||'—'}}</td><td>{{r.submitted_by}}</td><td>{{date(r.created_at)}}</td></tr></tbody></table></div>
</details>
<p v-if="!records.length" class="empty">还没有回传。实验员按已分发计划完成湿热复测后，由研究员在此录入。</p>
<section v-if="versions.length" class="retest-versions">
<article v-for="v in versions" :key="v.id">
<div class="entry-line"><small>ANALYSIS v{{v.version}} · {{v.created_by}} · {{date(v.created_at)}} · 覆盖{{v.detail.record_count}}条回传</small><span :class="['status',v.detail.conclusion]">{{retestConclusion[v.detail.conclusion]}}</span></div>
<p class="muted">配对不足{{v.detail.min_pairs}}对或不确定范围跨0时，不作改善或衰减结论。</p>
<ul class="metric-lines"><li v-for="(m,code) in v.detail.metrics" :key="code"><b>{{metricName(code)}}</b>（{{m.unit}}）{{statText(m)}} · <span :class="['status',m.conclusion]">{{retestConclusion[m.conclusion]}}</span></li></ul>
<details class="retest-detail"><summary>本版采用的明细 · {{v.detail.pairs.length}}对配对 / {{v.detail.exclusions.length}}条排除</summary>
<div class="table-scroll" v-if="v.detail.pairs.length"><table><thead><tr><th>记录</th><th>试件</th><th>指标</th><th>冻结前</th><th>复测</th><th>变化</th></tr></thead><tbody><tr v-for="p in v.detail.pairs" :key="p.record_id"><td>#{{p.record_id}}</td><td><b>{{p.code}}</b></td><td>{{metricName(p.metric)}}</td><td>{{num(p.pre,4)}}</td><td>{{num(p.post,4)}}</td><td>{{num(p.delta,4)}}</td></tr></tbody></table></div>
<div class="table-scroll" v-if="v.detail.exclusions.length"><table><thead><tr><th>记录</th><th>试件</th><th>指标</th><th>排除原因</th></tr></thead><tbody><tr v-for="e in v.detail.exclusions" :key="e.record_id"><td>#{{e.record_id}}</td><td><b>{{e.code}}</b></td><td>{{metricName(e.metric)}}</td><td>{{e.reason}}</td></tr></tbody></table></div>
<small class="fingerprint"><code>records {{v.detail.records_fingerprint}}</code></small>
</details>
<button class="text-link" @click="perform(()=>downloadRetest(note.id,v.version))">下载第{{v.version}}版结论 CSV ↙</button>
</article>
</section>
</details>
</template>
