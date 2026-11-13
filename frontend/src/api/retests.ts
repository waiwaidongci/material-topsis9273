import {request,post} from './client';import type {RetestRecord,RetestAnalysis,RetestSubmitResult} from '../types/domain';
export const records=(noteId:number)=>request<RetestRecord[]>('/notes/'+noteId+'/retests');
export const submit=(noteId:number,data:unknown)=>post<RetestSubmitResult>('/notes/'+noteId+'/retests',data);
export const analyses=(noteId:number)=>request<RetestAnalysis[]>('/notes/'+noteId+'/analyses');
export const analyze=(noteId:number)=>post<RetestAnalysis>('/notes/'+noteId+'/analyses',{});
