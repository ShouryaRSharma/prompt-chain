import React, { useState } from 'react';

const AddModelForm = ({ onSubmit, onCancel }) => {
  const [modelData, setModelData] = useState({
    name: '',
    system_prompt: '',
    user_prompt_schema: '',
    response_schema: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setModelData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const formattedData = {
      ...modelData,
      user_prompt_schema: JSON.parse(modelData.user_prompt_schema),
      response_schema: JSON.parse(modelData.response_schema)
    };
    onSubmit(formattedData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-2xl font-bold mb-4">Add New Model</h2>
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700">Name:</label>
        <input
          type="text"
          id="name"
          name="name"
          value={modelData.name}
          onChange={handleChange}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
          required
        />
      </div>
      <div>
        <label htmlFor="system_prompt" className="block text-sm font-medium text-gray-700">System Prompt:</label>
        <textarea
          id="system_prompt"
          name="system_prompt"
          value={modelData.system_prompt}
          onChange={handleChange}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
          rows="3"
          required
        />
      </div>
      <div>
        <label htmlFor="user_prompt_schema" className="block text-sm font-medium text-gray-700">User Prompt Schema (JSON):</label>
        <textarea
          id="user_prompt_schema"
          name="user_prompt_schema"
          value={modelData.user_prompt_schema}
          onChange={handleChange}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
          rows="3"
          required
        />
      </div>
      <div>
        <label htmlFor="response_schema" className="block text-sm font-medium text-gray-700">Response Schema (JSON):</label>
        <textarea
          id="response_schema"
          name="response_schema"
          value={modelData.response_schema}
          onChange={handleChange}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
          rows="3"
          required
        />
      </div>
      <div className="flex justify-end space-x-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Add Model
        </button>
      </div>
    </form>
  );
};

export default AddModelForm;
