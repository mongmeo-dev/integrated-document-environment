# LatexProjectResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**revision_id** | **string** |  | [default to undefined]
**document_id** | **string** |  | [default to undefined]
**entrypoint** | **string** |  | [default to undefined]
**source** | **string** |  | [default to undefined]
**source_sha256** | **string** |  | [default to undefined]
**files** | **Array&lt;string&gt;** |  | [default to undefined]
**origin** | [**RevisionOrigin**](RevisionOrigin.md) |  | [default to undefined]
**conversion_status** | [**ConversionStatus**](ConversionStatus.md) |  | [default to undefined]
**compile_status** | [**CompileStatus**](CompileStatus.md) |  | [default to undefined]
**compile_log** | **string** |  | [default to undefined]
**compiled_pdf_sha256** | **string** |  | [optional] [default to undefined]
**preview_available** | **boolean** |  | [default to undefined]
**created_at** | **string** |  | [default to undefined]

## Example

```typescript
import { LatexProjectResponse } from './api';

const instance: LatexProjectResponse = {
    revision_id,
    document_id,
    entrypoint,
    source,
    source_sha256,
    files,
    origin,
    conversion_status,
    compile_status,
    compile_log,
    compiled_pdf_sha256,
    preview_available,
    created_at,
};
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
