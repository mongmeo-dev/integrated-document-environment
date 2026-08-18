# ApprovalWorkflowResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **string** |  | [default to undefined]
**document_id** | **string** |  | [default to undefined]
**status** | [**ApprovalStatus**](ApprovalStatus.md) |  | [default to undefined]
**is_started** | **boolean** |  | [default to undefined]
**started_at** | **string** |  | [default to undefined]
**completed_at** | **string** |  | [default to undefined]
**created_at** | **string** |  | [default to undefined]
**updated_at** | **string** |  | [default to undefined]
**steps** | [**Array&lt;ApprovalStepResponse&gt;**](ApprovalStepResponse.md) |  | [optional] [default to undefined]

## Example

```typescript
import { ApprovalWorkflowResponse } from './api';

const instance: ApprovalWorkflowResponse = {
    id,
    document_id,
    status,
    is_started,
    started_at,
    completed_at,
    created_at,
    updated_at,
    steps,
};
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
