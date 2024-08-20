import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';

const ModelNode = ({ data }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-4 border border-gray-200">
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      <div className="font-bold text-lg mb-2">{data.label || 'Unnamed Model'}</div>
      {data.system_prompt && (
        <div className="text-sm text-gray-600 mb-2">
          System Prompt: {data.system_prompt.substring(0, 50)}...
        </div>
      )}
      {data.user_prompt_schema && (
        <div className="text-xs text-gray-500">
          Input Schema: {JSON.stringify(data.user_prompt_schema)}
        </div>
      )}
      {data.response_schema && (
        <div className="text-xs text-gray-500">
          Output Schema: {JSON.stringify(data.response_schema)}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
};

export default memo(ModelNode);
