/**
 * Lender create/edit form component.
 */

import { useState } from 'react';
import { Input, Button, Card } from '../ui';
import type { LenderCreate, LenderUpdate } from '../../types';

interface LenderFormProps {
  initialData?: Partial<LenderCreate | LenderUpdate>;
  isEditing?: boolean;
  onSubmit: (data: LenderCreate | LenderUpdate) => Promise<void>;
  onCancel: () => void;
}

export function LenderForm({
  initialData = {},
  isEditing = false,
  onSubmit,
  onCancel,
}: LenderFormProps) {
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    description: '',
    contact_email: '',
    contact_phone: '',
    ...initialData,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: '' }));
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!isEditing && !formData.id.trim()) {
      newErrors.id = 'ID is required';
    } else if (!isEditing && !/^[a-z0-9_]+$/.test(formData.id)) {
      newErrors.id = 'ID must contain only lowercase letters, numbers, and underscores';
    }

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (formData.contact_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.contact_email)) {
      newErrors.contact_email = 'Invalid email format';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    setIsSubmitting(true);
    try {
      const submitData = isEditing
        ? {
            name: formData.name,
            description: formData.description || undefined,
            contact_email: formData.contact_email || undefined,
            contact_phone: formData.contact_phone || undefined,
          }
        : {
            id: formData.id,
            name: formData.name,
            description: formData.description || undefined,
            contact_email: formData.contact_email || undefined,
            contact_phone: formData.contact_phone || undefined,
          };

      await onSubmit(submitData);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card padding="lg">
      <form onSubmit={handleSubmit}>
        <div className="space-y-6">
          {!isEditing && (
            <Input
              label="Lender ID"
              type="text"
              value={formData.id}
              onChange={(e) => handleChange('id', e.target.value)}
              error={errors.id}
              helperText="Unique identifier (lowercase, numbers, underscores only)"
              required
            />
          )}

          <Input
            label="Name"
            type="text"
            value={formData.name}
            onChange={(e) => handleChange('name', e.target.value)}
            error={errors.name}
            required
          />

          <Input
            label="Description"
            type="text"
            value={formData.description}
            onChange={(e) => handleChange('description', e.target.value)}
            error={errors.description}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <Input
              label="Contact Email"
              type="email"
              value={formData.contact_email}
              onChange={(e) => handleChange('contact_email', e.target.value)}
              error={errors.contact_email}
            />

            <Input
              label="Contact Phone"
              type="tel"
              value={formData.contact_phone}
              onChange={(e) => handleChange('contact_phone', e.target.value)}
              error={errors.contact_phone}
            />
          </div>
        </div>

        <div className="mt-6 flex justify-end space-x-3">
          <Button type="button" variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" isLoading={isSubmitting}>
            {isEditing ? 'Save Changes' : 'Create Lender'}
          </Button>
        </div>
      </form>
    </Card>
  );
}

export default LenderForm;
