# FormatCheckResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **string** |  | [default to undefined]
**external_edit_result_id** | **string** |  | [default to undefined]
**automatic_check_completed** | **boolean** |  | [default to undefined]
**visual_review** | [**VisualReviewStatus**](VisualReviewStatus.md) |  | [default to undefined]
**unresolved_difference_count** | **number** |  | [default to undefined]
**created_at** | **string** |  | [default to undefined]
**updated_at** | **string** |  | [default to undefined]
**differences** | [**Array&lt;FormatDifferenceResponse&gt;**](FormatDifferenceResponse.md) |  | [optional] [default to undefined]

## Example

```typescript
import { FormatCheckResponse } from './api';

const instance: FormatCheckResponse = {
    id,
    external_edit_result_id,
    automatic_check_completed,
    visual_review,
    unresolved_difference_count,
    created_at,
    updated_at,
    differences,
};
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
