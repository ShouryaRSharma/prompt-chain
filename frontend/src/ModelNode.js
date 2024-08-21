import React, { memo, useState } from 'react';
import { Handle, Position } from 'reactflow';

const ModelNode = ({ data }) => {
  const [expanded, setExpanded] = useState(false);

  const toggleExpand = () => {
    setExpanded(!expanded);
  };

  return (
    <div 
      className={`bg-white rounded-lg shadow-md p-4 border border-gray-200 cursor-pointer transition-all duration-300 ease-in-out ${expanded ? 'w-96' : 'w-64'}`}
      onClick={toggleExpand}
    >
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      <div className="font-bold text-lg mb-2">{data.label || 'Unnamed Model'}</div>
      {expanded ? (
        <>
          <div className="text-sm text-gray-600 mb-2">
            <strong>System Prompt:</strong> {data.system_prompt}
          </div>
          <div className="text-sm text-gray-600 mb-2">
            <strong>Input Schema:</strong> 
            <pre className="text-xs bg-gray-100 p-2 rounded mt-1 overflow-auto max-h-40">
              {JSON.stringify(data.user_prompt_schema, null, 2)}
            </pre>
          </div>
          <div className="text-sm text-gray-600">
            <strong>Output Schema:</strong> 
            <pre className="text-xs bg-gray-100 p-2 rounded mt-1 overflow-auto max-h-40">
              {JSON.stringify(data.response_schema, null, 2)}
            </pre>
          </div>
        </>
      ) : (
        <>
          {data.system_prompt && (
            <div className="text-sm text-gray-600 mb-2">
              System Prompt: {data.system_prompt.substring(0, 50)}...
            </div>
          )}
          <div className="text-xs text-gray-500">
            Click to see more details
          </div>
        </>
      )}
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
};

export default memo(ModelNode);
