import { useState, useEffect, useRef } from 'react';
import { X, Plus } from 'lucide-react';

const SCHEMAS = [
    { name: 'invoice', display_name: 'Invoice' },
    { name: 'identity', display_name: 'Identity' },
    { name: 'resume', display_name: 'Resume' },
    { name: 'medical', display_name: 'Medical' },
    { name: 'custom', display_name: 'Custom' },
];

const INITIAL_FIELDS = {
    invoice: ['invoice_no', 'vendor_name', 'total_amount', 'tax_id'],
    identity: ['document_number', 'first_name', 'last_name', 'date_of_birth', 'expiry_date'],
    resume: ['candidate_name', 'email', 'phone', 'skills', 'education'],
    medical: ['patient_name', 'date_of_service', 'diagnosis', 'provider_name'],
    custom: ['invoice_no', 'vendor_name', 'total_amount', 'tax_id'],
};

export default function FieldSelector({ onSchemaChange }) {
    const [selectedSchema, setSelectedSchema] = useState('invoice');
    const [schemaFields, setSchemaFields] = useState(INITIAL_FIELDS);
    const [isAddingField, setIsAddingField] = useState(false);
    const [newFieldName, setNewFieldName] = useState('');
    const inputRef = useRef(null);

    // Trigger initial schema change notification
    useEffect(() => {
        onSchemaChange('invoice', INITIAL_FIELDS.invoice);
    }, []);

    const handleSelectSchema = (schema) => {
        setSelectedSchema(schema);
        onSchemaChange(schema, schemaFields[schema] || []);
    };

    const handleAddField = (e) => {
        if (e) e.preventDefault();
        const trimmed = newFieldName.trim();
        if (!trimmed) {
            setIsAddingField(false);
            return;
        }

        const currentFields = schemaFields[selectedSchema] || [];
        if (!currentFields.includes(trimmed)) {
            const updatedFields = [...currentFields, trimmed];
            const updatedSchemaFields = {
                ...schemaFields,
                [selectedSchema]: updatedFields
            };
            setSchemaFields(updatedSchemaFields);
            onSchemaChange(selectedSchema, updatedFields);
        }
        setNewFieldName('');
        setIsAddingField(false);
    };

    const handleRemoveField = (fieldToRemove) => {
        const currentFields = schemaFields[selectedSchema] || [];
        const updatedFields = currentFields.filter((f) => f !== fieldToRemove);
        const updatedSchemaFields = {
            ...schemaFields,
            [selectedSchema]: updatedFields
        };
        setSchemaFields(updatedSchemaFields);
        onSchemaChange(selectedSchema, updatedFields);
    };

    // Focus effect for add field input
    useEffect(() => {
        if (isAddingField && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isAddingField]);

    const activeFields = schemaFields[selectedSchema] || [];

    return (
        <div className="space-y-6">
            {/* Configuration pills */}
            <div className="space-y-3">
                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest">
                    Configuration
                </h3>
                <div className="bg-slate-50 border border-gray-200 rounded-lg p-1.5 flex flex-wrap gap-1.5">
                    {SCHEMAS.map((s) => {
                        const isActive = selectedSchema === s.name;
                        return (
                            <button
                                key={s.name}
                                type="button"
                                onClick={() => handleSelectSchema(s.name)}
                                className={`text-xs font-semibold px-4 py-2 rounded-md transition-all cursor-pointer active:scale-95
                  ${isActive
                                        ? 'bg-[#5850ec] text-white shadow-sm'
                                        : 'text-gray-655 hover:text-gray-900 bg-transparent hover:bg-gray-100/50'
                                    }
                `}
                            >
                                {s.display_name}
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Extractable Fields List */}
            <div className="space-y-3">
                <h3 className="text-xs font-bold text-gray-550 uppercase tracking-widest">
                    Extractable Fields
                </h3>
                <div className="flex flex-wrap gap-2.5 items-center min-h-[38px]">
                    {activeFields.map((field) => (
                        <div
                            key={field}
                            className="bg-white border border-indigo-200 text-[#5850ec] text-xs font-semibold px-3 py-1.5 rounded-md flex items-center justify-between gap-1.5 shadow-sm"
                        >
                            <span>{field}</span>
                            <button
                                type="button"
                                onClick={() => handleRemoveField(field)}
                                className="hover:text-red-500 transition-colors cursor-pointer"
                            >
                                <X size={13} />
                            </button>
                        </div>
                    ))}

                    {/* Inline add field controller */}
                    {isAddingField ? (
                        <form
                            onSubmit={handleAddField}
                            onBlur={() => setTimeout(handleAddField, 150)}
                            className="inline-block"
                        >
                            <input
                                ref={inputRef}
                                type="text"
                                value={newFieldName}
                                placeholder="Field name"
                                onChange={(e) => setNewFieldName(e.target.value)}
                                className="bg-white border border-indigo-300 text-xs font-semibold px-2.5 py-1.5 rounded-md outline-none focus:ring-1 focus:ring-indigo-500 w-24 text-gray-800"
                            />
                        </form>
                    ) : (
                        <button
                            type="button"
                            onClick={() => setIsAddingField(true)}
                            className="bg-white border border-dashed border-indigo-300 text-[#5850ec] hover:bg-slate-50 text-xs font-semibold px-3 py-1.5 rounded-md flex items-center justify-center gap-1 cursor-pointer transition-all shadow-sm active:scale-95"
                        >
                            <Plus size={13} />
                            <span>Add Field</span>
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
