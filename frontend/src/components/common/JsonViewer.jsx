import React from 'react';
import ReactJson from 'react-json-view';

const JsonViewer = ({ data }) => {
  return (
    <div className="p-4 h-full overflow-auto">
      <ReactJson
        src={data}
        theme="tomorrow"
        iconStyle="circle"
        displayDataTypes={false}
        name={false}
        style={{ backgroundColor: 'transparent', width: '100%' }}
      />
    </div>
  );
};

export default JsonViewer;