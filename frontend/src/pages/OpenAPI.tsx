import React, { useEffect, useState } from 'react';
import { OpenAPISpec } from '../types';
import { getOpenAPISpecs } from '../api/client';
import { Badge } from '../components/Badge';
import { FileCode, Tag } from 'lucide-react';

export const OpenAPI: React.FC = () => {
  const [specs, setSpecs] = useState<OpenAPISpec[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOpenAPISpecs()
      .then(data => setSpecs(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6 font-mono text-xs">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <FileCode size={20} className="text-indigo-400" />
            <span>OPENAPI SPECIFICATIONS & OPERATIONS</span>
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            Structural endpoint models parsed for transaction operation mapping
          </p>
        </div>
        <span className="text-slate-500">{specs.length} Specifications Loaded</span>
      </div>

      <div className="space-y-4">
        {specs.map((spec) => (
          <div key={spec.id} className="bg-slate-900 border border-slate-800 rounded-lg p-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
              <div>
                <h3 className="text-sm font-bold text-slate-100">{spec.title} (v{spec.version})</h3>
                <span className="text-[11px] text-slate-500">ID: {spec.id}</span>
              </div>
              <Badge variant="info">{spec.operations.length} Operations</Badge>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {spec.operations.map((op) => (
                <div key={op.id} className="p-3 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge variant={op.method === 'GET' ? 'info' : op.method === 'POST' ? 'success' : 'warning'}>
                        {op.method}
                      </Badge>
                      <span className="font-semibold text-slate-200">{op.path_template}</span>
                    </div>
                    {op.summary && <div className="text-[10px] text-slate-400">{op.summary}</div>}
                  </div>
                  <span className="text-[10px] text-cyan-400 font-medium">{op.operation_id}</span>
                </div>
              ))}
            </div>
          </div>
        ))}

        {specs.length === 0 && (
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-8 text-center text-slate-400">
            <FileCode size={32} className="mx-auto mb-2 text-indigo-400" />
            <p className="font-semibold text-slate-200">No OpenAPI Specifications Loaded</p>
            <p className="text-[11px] text-slate-500 mt-1 max-w-md mx-auto">
              Upload an OpenAPI specification file on the Overview screen to map HTTP traffic endpoints to operational path templates like <code className="text-cyan-400">/projects/&#123;project_id&#125;</code>.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
