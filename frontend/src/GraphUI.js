import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, { 
  Controls, 
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  ReactFlowProvider
} from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';
import ModelNode from './ModelNode';
import AddModelForm from './AddModelForm';
import AddChainForm from './AddChainForm';

const API_BASE = "http://localhost:8000";

const nodeTypes = {
  modelNode: ModelNode,
};

const GraphUIContent = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [models, setModels] = useState([]);
  const [chains, setChains] = useState([]);
  const [showAddModel, setShowAddModel] = useState(false);
  const [showAddChain, setShowAddChain] = useState(false);
  const [selectedChain, setSelectedChain] = useState('');
  const [showChainExecutionModal, setShowChainExecutionModal] = useState(false);
  const [chainInput, setChainInput] = useState('');
  const [chainResult, setChainResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    fetchModels();
    fetchChains();
  }, []);

  const fetchModels = async () => {
    try {
      const response = await axios.get(`${API_BASE}/get_models`);
      setModels(response.data.models);
      
      const modelDetails = await Promise.all(
        response.data.models.map(modelName => 
          axios.get(`${API_BASE}/get_model/${modelName}`).then(res => res.data)
        )
      );

      const modelNodes = modelDetails.map((model, index) => ({
        id: `model-${model.name}`,
        type: 'modelNode',
        data: { 
          label: model.name,
          system_prompt: model.system_prompt,
          user_prompt_schema: model.user_prompt,
          response_schema: model.response,
          expanded: false
        },
        position: { x: 100 + (index * 450), y: 200 + (index * 200) },
      }));
      setNodes(modelNodes);
    } catch (error) {
      console.error("Error fetching models:", error);
      setErrorMessage("Failed to fetch models. Please try again.");
    }
  };

  const fetchChains = async () => {
    try {
      const response = await axios.get(`${API_BASE}/get_chains`);
      setChains(response.data.chains);
    } catch (error) {
      console.error("Error fetching chains:", error);
      setErrorMessage("Failed to fetch chains. Please try again.");
    }
  };

  const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  const handleAddModel = async (modelData) => {
    try {
      await axios.post(`${API_BASE}/create_model`, modelData);
      await fetchModels();
      setShowAddModel(false);
    } catch (error) {
      console.error("Error creating model:", error);
      setErrorMessage("Failed to create model. Please try again.");
    }
  };

  const handleAddChain = async (chainData) => {
    try {
      await axios.post(`${API_BASE}/create_chain`, chainData);
      await fetchChains();
      setShowAddChain(false);
    } catch (error) {
      console.error("Error creating chain:", error);
      setErrorMessage("Failed to create chain. Please try again.");
    }
  };

  const handleChainSelection = async (e) => {
    const chainName = e.target.value;
    setSelectedChain(chainName);
    if (chainName) {
      try {
        const response = await axios.get(`${API_BASE}/get_chain/${chainName}`);
        const chainData = response.data;
        
        const newEdges = chainData.steps.map((step, index) => ({
          id: `e${index}`,
          source: `model-${step.name}`,
          target: index < chainData.steps.length - 1 ? `model-${chainData.steps[index + 1].name}` : null,
          animated: true,
          style: { stroke: '#ff00ff' }
        })).filter(edge => edge.target !== null);

        setEdges(newEdges);

        setNodes((nds) => nds.map(node => {
          if (chainData.steps.some(step => `model-${step.name}` === node.id)) {
            return { ...node, style: { border: '2px solid #ff00ff' } };
          }
          return node;
        }));
      } catch (error) {
        console.error("Error fetching chain details:", error);
        setErrorMessage("Failed to fetch chain details. Please try again.");
      }
    } else {
      setEdges([]);
      setNodes((nds) => nds.map(node => ({ ...node, style: {} })));
    }
  };

  const handleChainInputChange = (e) => {
    setChainInput(e.target.value);
    setErrorMessage('');
  };

  const formatJSON = () => {
    try {
      const sanitizedInput = chainInput.replace(/\n/g, "\\n");
      const parsed = JSON.parse(sanitizedInput);
      const formatted = JSON.stringify(parsed, null, 2);
      setChainInput(formatted);
      setErrorMessage('');
    } catch (error) {
      setErrorMessage(`Invalid JSON: ${error.message}`);
    }
  };

  const runChain = async () => {
    if (!selectedChain || !chainInput) {
      setErrorMessage('Please select a chain and provide input');
      return;
    }

    try {
      let parsedInput;
      try {
        const sanitizedInput = chainInput.replace(/\n/g, "\\n");
        parsedInput = JSON.parse(sanitizedInput);
      } catch (parseError) {
        setErrorMessage(`Invalid JSON input: ${parseError.message}`);
        return;
      }

      const response = await axios.post(`${API_BASE}/execute_chain`, {
        chain_name: selectedChain,
        initial_input: parsedInput
      });
      setChainResult(response.data.result);
      setErrorMessage('');
    } catch (error) {
      console.error("Error running chain:", error);
      setErrorMessage(`Error running chain: ${error.response?.data?.detail || error.message}`);
    }
  };

  const onNodeClick = useCallback((event, node) => {
    setNodes((nds) =>
      nds.map((n) => {
        if (n.id === node.id) {
          return {
            ...n,
            data: {
              ...n.data,
              expanded: !n.data.expanded,
            },
          };
        }
        return n;
      })
    );
    
    setTimeout(() => {
      const expandedNode = nodes.find(n => n.id === node.id);
      if (expandedNode && expandedNode.data.expanded) {
        setNodes((nds) =>
          nds.map((n) => {
            if (n.id !== node.id) {
              const dx = n.position.x - node.position.x;
              const dy = n.position.y - node.position.y;
              const distance = Math.sqrt(dx * dx + dy * dy);
              if (distance < 300) {
                const angle = Math.atan2(dy, dx);
                return {
                  ...n,
                  position: {
                    x: n.position.x + Math.cos(angle) * (300 - distance),
                    y: n.position.y + Math.sin(angle) * (300 - distance),
                  },
                };
              }
            }
            return n;
          })
        );
      }
    }, 300);
  }, [nodes, setNodes]);

  return (
    <div className="w-full h-screen flex flex-col">
      <div className="p-4 bg-gray-100 flex justify-between items-center">
        <div>
          <button 
            onClick={() => setShowAddModel(true)} 
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition mr-2"
          >
            Add Model
          </button>
          <button 
            onClick={() => setShowAddChain(true)} 
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 transition"
          >
            Add Chain
          </button>
        </div>
        <div className="flex items-center">
          <select 
            value={selectedChain} 
            onChange={handleChainSelection}
            className="mr-2 p-2 border rounded"
          >
            <option value="">Select a Chain</option>
            {chains.map(chain => (
              <option key={chain} value={chain}>{chain}</option>
            ))}
          </select>
          <button 
            onClick={() => setShowChainExecutionModal(true)}
            className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600 transition"
            disabled={!selectedChain}
          >
            Execute Chain
          </button>
        </div>
      </div>
      <div className="flex-grow">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
        >
          <Controls />
          <Background variant="dots" gap={12} size={1} />
        </ReactFlow>
      </div>
      {showAddModel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl max-w-md w-full">
            <AddModelForm onSubmit={handleAddModel} onCancel={() => setShowAddModel(false)} />
          </div>
        </div>
      )}
      {showAddChain && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl max-w-md w-full">
            <AddChainForm onSubmit={handleAddChain} onCancel={() => setShowAddChain(false)} availableModels={models} />
          </div>
        </div>
      )}
      {showChainExecutionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-auto">
            <h2 className="text-2xl font-bold mb-4">Execute Chain: {selectedChain}</h2>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Chain Input (JSON):
              </label>
              <div className="flex">
                <textarea
                  value={chainInput}
                  onChange={handleChainInputChange}
                  className="flex-grow h-40 p-2 border rounded-l font-mono text-sm"
                  placeholder="Enter your JSON input here"
                />
                <div className="w-10 flex flex-col">
                  <button 
                    onClick={formatJSON}
                    className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded-tr"
                    title="Format JSON"
                  >
                    { }
                  </button>
                  <button 
                    onClick={() => {
                      setChainInput('');
                      setErrorMessage('');
                    }}
                    className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded-br"
                    title="Clear"
                  >
                    ×
                  </button>
                </div>
              </div>
              {errorMessage && (
                <div className="mt-2 text-red-600 text-sm">{errorMessage}</div>
              )}
            </div>
            <div className="flex justify-between mb-4">
              <button
                onClick={() => {
                  setShowChainExecutionModal(false);
                  setErrorMessage('');
                }}
                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 transition"
              >
                Cancel
              </button>
              <button
                onClick={runChain}
                className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600 transition"
              >
                Run Chain
              </button>
            </div>
            {chainResult && (
              <div>
                <h3 className="font-bold mb-2">Chain Execution Result:</h3>
                <pre className="bg-gray-100 p-4 rounded overflow-auto max-h-60 font-mono text-sm">
                  {JSON.stringify(chainResult, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const GraphUI = () => (
  <ReactFlowProvider>
    <GraphUIContent />
  </ReactFlowProvider>
);

export default GraphUI;
