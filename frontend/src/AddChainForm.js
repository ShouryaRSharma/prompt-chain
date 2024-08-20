import React, { useState } from 'react';

const AddChainForm = ({ onSubmit, onCancel, availableModels }) => {
  const [chainData, setChainData] = useState({
    name: '',
    steps: [{ name: '', input_mapping: '' }],
    final_output_mapping: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setChainData(prev => ({ ...prev, [name]: value }));
  };

  const handleStepChange = (index, field, value) => {
    setChainData(prev => {
      const newSteps = [...prev.steps];
      newSteps[index] = { ...newSteps[index], [field]: value };
      return { ...prev, steps: newSteps };
    });
  };

  const addStep = () => {
    setChainData(prev => ({
      ...prev,
      steps: [...prev.steps, { name: '', input_mapping: '' }]
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const formattedData = {
      ...chainData,
      steps: chainData.steps.map(step => ({
        ...step,
        input_mapping: JSON.parse(step.input_mapping)
      })),
      final_output_mapping: JSON.parse(chainData.final_output_mapping)
    };
    onSubmit(formattedData);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-md w-full max-w-lg max-h-screen overflow-y-auto">
      <h2 className="text-2xl font-bold mb-4">Add New Chain</h2>
      <div className="mb-4">
        <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="name">
          Chain Name:
        </label>
        <input
          type="text"
          id="name"
          name="name"
          value={chainData.name}
          onChange={handleChange}
          className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          required
        />
      </div>
      {chainData.steps.map((step, index) => (
        <div key={index} className="mb-4 p-4 border rounded">
          <h3 className="font-bold mb-2">Step {index + 1}</h3>
          <div className="mb-2">
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Model:
            </label>
            <select
              value={step.name}
              onChange={(e) => handleStepChange(index, 'name', e.target.value)}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              required
            >
              <option value="">Select a model</option>
              {availableModels.map(model => (
                <option key={model} value={model}>{model}</option>
              ))}
            </select>
          </div>
          <div className="mb-2">
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Input Mapping (JSON):
            </label>
            <textarea
              value={step.input_mapping}
              onChange={(e) => handleStepChange(index, 'input_mapping', e.target.value)}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              required
            />
          </div>
        </div>
      ))}
      <button
        type="button"
        onClick={addStep}
        className="mb-4 bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded inline-flex items-center"
      >
        Add Step
      </button>
      <div className="mb-4">
        <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="final_output_mapping">
          Final Output Mapping (JSON):
        </label>
        <textarea
          id="final_output_mapping"
          name="final_output_mapping"
          value={chainData.final_output_mapping}
          onChange={handleChange}
          className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          required
        />
      </div>
      <div className="flex items-center justify-between">
        <button
          type="submit"
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
        >
          Add Chain
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
        >
          Cancel
        </button>
      </div>
    </form>
  );
};

export default AddChainForm;
