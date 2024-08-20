import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge
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

const GraphUI = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [models, setModels] = useState([]);
  const [chains, setChains] = useState([]);
  const [showAddModel, setShowAddModel] = useState(false);
  const [showAddChain, setShowAddChain] = useState(false);
  const [selectedChain, setSelectedChain] = useState('');
  const [chainInput, setChainInput] = useState('');
  const [chainResult, setChainResult] = useState(null);

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
          user_prompt_schema: model.user_prompt_schema,
          response_schema: model.response_schema
        },
        position: { x: 100 + (index * 200), y: 100 + (index * 100) },
      }));
      setNodes(modelNodes);
    } catch (error) {
      console.error("Error fetching models:", error);
    }
  };

  const fetchChains = async () => {
    try {
      const response = await axios.get(`${API_BASE}/get_chains`);
      setChains(response.data.chains);
    } catch (error) {
      console.error("Error fetching chains:", error);
    }
  };

  const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  const addModelNode = async (modelData) => {
    try {
      const response = await axios.get(`${API_BASE}/get_model/${modelData.name}`);
      const fullModelData = response.data;

      const newNode = {
        id: `model-${fullModelData.name}`,
        type: 'modelNode',
        data: {
          label: fullModelData.name,
          system_prompt: fullModelData.system_prompt,
          user_prompt_schema: fullModelData.user_prompt_schema,
          response_schema: fullModelData.response_schema
        },
        position: { x: Math.random() * 500, y: Math.random() * 500 },
      };
      setNodes((nds) => nds.concat(newNode));
    } catch (error) {
      console.error("Error fetching new model details:", error);
    }
  };

  const handleAddModel = async (modelData) => {
    try {
      await axios.post(`${API_BASE}/create_model`, modelData);
      await fetchModels();
      await addModelNode(modelData);
      setShowAddModel(false);
    } catch (error) {
      console.error("Error creating model:", error);
    }
  };

  const handleAddChain = async (chainData) => {
    try {
      await axios.post(`${API_BASE}/create_chain`, chainData);
      await fetchChains();
      setShowAddChain(false);
    } catch (error) {
      console.error("Error creating chain:", error);
    }
  };

  const handleChainSelection = async (e) => {
    const chainName = e.target.value;
    setSelectedChain(chainName);
    if (chainName) {
      try {
        const response = await axios.get(`${API_BASE}/get_chain/${chainName}`);
        const chainData = response.data;

        // Reset node styles
        setNodes((nds) => nds.map(node => ({ ...node, style: {} })));

        // Create edges based on chain steps
        const newEdges = chainData.steps.map((step, index) => ({
          id: `e${index}`,
          source: `model-${step.name}`,
          target: index < chainData.steps.length - 1 ? `model-${chainData.steps[index + 1].name}` : null,
          animated: true,
          style: { stroke: '#ff00ff' }
        })).filter(edge => edge.target !== null);

        setEdges(newEdges);

        // Highlight nodes that are part of the chain
        setNodes((nds) => nds.map(node => {
          if (chainData.steps.some(step => `model-${step.name}` === node.id)) {
            return { ...node, style: { border: '2px solid #ff00ff' } };
          }
          return node;
        }));
      } catch (error) {
        console.error("Error fetching chain details:", error);
      }
    } else {
      // Reset edges and node styles when no chain is selected
      setEdges([]);
      setNodes((nds) => nds.map(node => ({ ...node, style: {} })));
    }
  };

  const handleChainInputChange = (e) => {
    setChainInput(e.target.value);
  };

  const runChain = async () => {
    if (!selectedChain || !chainInput) {
      alert('Please select a chain and provide input');
      return;
    }

    try {
      const response = await axios.post(`${API_BASE}/execute_chain`, {
        chain_name: selectedChain,
        initial_input: JSON.parse(chainInput)
      });
      setChainResult(response.data.result);
    } catch (error) {
      console.error("Error running chain:", error);
      alert('Error running chain. Please check the console for details.');
    }
  };

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
          <input
            type="text"
            value={chainInput}
            onChange={handleChainInputChange}
            placeholder="Chain Input (JSON)"
            className="mr-2 p-2 border rounded"
          />
          <button
            onClick={runChain}
            className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600 transition"
          >
            Run Chain
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
          nodeTypes={nodeTypes}
        >
          <Controls />
          <MiniMap />
          <Background variant="dots" gap={12} size={1} />
        </ReactFlow>
      </div>
      {chainResult && (
        <div className="p-4 bg-gray-100 border-t">
          <h3 className="font-bold mb-2">Chain Execution Result:</h3>
          <pre className="bg-white p-2 rounded overflow-auto max-h-40">
            {JSON.stringify(chainResult, null, 2)}
          </pre>
        </div>
      )}
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
    </div>
  );
};

export default GraphUI;
