import axios from 'axios';
import {
  Target, Identity, Session, Transaction, OpenAPISpec,
  Dependency, Workflow, WorkflowGraphResponse, ShadowWorkflow
} from '../types';
import { AUTHTWIN_CONFIG } from '../config';

const api = axios.create({
  baseURL: AUTHTWIN_CONFIG.API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getHealth = async () => (await api.get('/health')).data;

export const getTargets = async (): Promise<Target[]> => (await api.get('/targets')).data;
export const getActiveTarget = async (): Promise<Target | null> => {
  try {
    return (await api.get('/targets/active')).data;
  } catch (err: any) {
    if (err.response?.status === 404) {
      return null;
    }
    throw err;
  }
};
export const setActiveTarget = async (targetUrl: string): Promise<Target> =>
  (await api.post('/targets/active', { target_url: targetUrl })).data;
export const createTarget = async (data: { name: string; base_url: string; allowed_host_regex?: string }): Promise<Target> =>
  (await api.post('/targets', data)).data;

export const getIdentities = async (targetId?: string): Promise<Identity[]> =>
  (await api.get('/identities', { params: { target_id: targetId } })).data;
export const createIdentity = async (data: { target_id?: string; name: string; role: string; auth_type?: string }): Promise<Identity> =>
  (await api.post('/identities', data)).data;
export const deleteIdentity = async (identityId: string) =>
  (await api.delete(`/identities/${identityId}`)).data;


export const getSessions = async (targetId?: string): Promise<Session[]> =>
  (await api.get('/sessions', { params: { target_id: targetId } })).data;

export const getTransactions = async (sessionId?: string): Promise<Transaction[]> =>
  (await api.get('/transactions', { params: { session_id: sessionId } })).data;
export const getTransaction = async (id: string): Promise<Transaction> =>
  (await api.get(`/transactions/${id}`)).data;

export const importHAR = async (file: File, targetId?: string, identityId?: string) => {
  const formData = new FormData();
  formData.append('file', file);
  if (targetId) formData.append('target_id', targetId);
  if (identityId) formData.append('identity_id', identityId);
  return (await api.post('/import/har', formData, { headers: { 'Content-Type': 'multipart/form-data' } })).data;
};

export const importOpenAPI = async (file: File, targetId?: string): Promise<OpenAPISpec> => {
  const formData = new FormData();
  formData.append('file', file);
  if (targetId) formData.append('target_id', targetId);
  return (await api.post('/import/openapi', formData, { headers: { 'Content-Type': 'multipart/form-data' } })).data;
};

export const getOpenAPISpecs = async (targetId?: string): Promise<OpenAPISpec[]> =>
  (await api.get('/openapi/specs', { params: { target_id: targetId } })).data;

export const getDependencies = async (sessionId?: string): Promise<Dependency[]> =>
  (await api.get('/dependencies', { params: { session_id: sessionId } })).data;

export const getWorkflows = async (): Promise<Workflow[]> => (await api.get('/workflows')).data;
export const getWorkflowGraph = async (id: string): Promise<WorkflowGraphResponse> =>
  (await api.get(`/workflows/${id}/graph`)).data;

export const cloneWorkflow = async (workflowId: string, shadowIdentityId: string): Promise<ShadowWorkflow> =>
  (await api.post(`/workflows/${workflowId}/clone`, { shadow_identity_id: shadowIdentityId })).data;

export const getShadowWorkflows = async (): Promise<ShadowWorkflow[]> => (await api.get('/shadow-workflows')).data;

export const deleteTarget = async (id: string) => (await api.delete(`/targets/${id}`)).data;

export const verifyTargetServer = async (targetUrl: string) =>
  (await api.post('/targets/probe', { target_url: targetUrl })).data;

export const probeTargetServer = verifyTargetServer;

export const startLiveRecording = async (identityId?: string) =>
  (await api.post('/interceptor/start-recording', null, { params: { identity_id: identityId } })).data;

export const pauseLiveRecording = async () =>
  (await api.post('/interceptor/pause-recording')).data;

export const resumeLiveRecording = async () =>
  (await api.post('/interceptor/resume-recording')).data;

export const clearLiveBuffer = async () =>
  (await api.post('/interceptor/clear-buffer')).data;

export const restartLiveRecording = async (identityId?: string) =>
  (await api.post('/interceptor/restart-recording', null, { params: { identity_id: identityId } })).data;

export const getLiveBuffer = async () =>
  (await api.get('/interceptor/live-buffer')).data;

export const stopLiveRecording = async () =>
  (await api.post('/interceptor/stop-recording')).data;

export const captureLiveSession = async (payload: { target_url: string; identity_id?: string; identity_name?: string; transactions: any[] }) =>
  (await api.post('/interceptor/capture-session', payload)).data;

export const deleteSession = async (sessionId: string) =>
  (await api.delete(`/sessions/${sessionId}`)).data;

export const deleteAllSessions = async () =>
  (await api.delete('/sessions')).data;

export const deleteWorkflow = async (workflowId: string) =>
  (await api.delete(`/workflows/${workflowId}`)).data;

export const deleteAllWorkflows = async () =>
  (await api.delete('/workflows')).data;



