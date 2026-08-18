# FormattingApi

All URIs are relative to *http://localhost*

|Method | HTTP request | Description|
|------------- | ------------- | -------------|
|[**collectExternalEditResult**](#collectexternaleditresult) | **POST** /api/v1/formatting/external-results | Collect External Edit Result|
|[**completeExternalResultVisualReview**](#completeexternalresultvisualreview) | **PATCH** /api/v1/formatting/external-results/{external_edit_result_id}/visual-review | Complete Visual Review|
|[**getExternalEditResult**](#getexternaleditresult) | **GET** /api/v1/formatting/external-results/{external_edit_result_id} | Get External Edit Result|
|[**getExternalResultApprovalAllowed**](#getexternalresultapprovalallowed) | **GET** /api/v1/formatting/external-results/{external_edit_result_id}/approval-allowed | Get Approval Allowed|
|[**getExternalResultFormatCheck**](#getexternalresultformatcheck) | **GET** /api/v1/formatting/external-results/{external_edit_result_id}/format-check | Get Format Check|
|[**listExternalEditResults**](#listexternaleditresults) | **GET** /api/v1/formatting/documents/{document_id}/external-results | List External Edit Results|
|[**resolveExternalResultFormatDifference**](#resolveexternalresultformatdifference) | **POST** /api/v1/formatting/differences/{difference_id}/resolve | Resolve Difference|
|[**runExternalResultAutomaticFormatCheck**](#runexternalresultautomaticformatcheck) | **POST** /api/v1/formatting/external-results/{external_edit_result_id}/automatic-check | Run Automatic Check|

# **collectExternalEditResult**
> { [key: string]: any | null; } collectExternalEditResult()


### Example

```typescript
import {
    FormattingApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new FormattingApi(configuration);

let documentId: string; // (default to undefined)
let documentVersionId: string; // (default to undefined)
let file: File; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.collectExternalEditResult(
    documentId,
    documentVersionId,
    file,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **documentId** | [**string**] |  | defaults to undefined|
| **documentVersionId** | [**string**] |  | defaults to undefined|
| **file** | [**File**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**{ [key: string]: any | null; }**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**202** | Successful Response |  -  |
|**400** | Bad Request |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**409** | Conflict |  -  |
|**413** | Content Too Large |  -  |
|**503** | Service Unavailable |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **completeExternalResultVisualReview**
> FormatCheckResponse completeExternalResultVisualReview(bodyCompleteExternalResultVisualReview)


### Example

```typescript
import {
    FormattingApi,
    Configuration,
    BodyCompleteExternalResultVisualReview
} from './api';

const configuration = new Configuration();
const apiInstance = new FormattingApi(configuration);

let externalEditResultId: string; // (default to undefined)
let bodyCompleteExternalResultVisualReview: BodyCompleteExternalResultVisualReview; //
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.completeExternalResultVisualReview(
    externalEditResultId,
    bodyCompleteExternalResultVisualReview,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **bodyCompleteExternalResultVisualReview** | **BodyCompleteExternalResultVisualReview**|  | |
| **externalEditResultId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**FormatCheckResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**409** | Conflict |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getExternalEditResult**
> ExternalEditResultResponse getExternalEditResult()


### Example

```typescript
import {
    FormattingApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new FormattingApi(configuration);

let externalEditResultId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.getExternalEditResult(
    externalEditResultId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **externalEditResultId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**ExternalEditResultResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getExternalResultApprovalAllowed**
> { [key: string]: boolean; } getExternalResultApprovalAllowed()


### Example

```typescript
import {
    FormattingApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new FormattingApi(configuration);

let externalEditResultId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.getExternalResultApprovalAllowed(
    externalEditResultId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **externalEditResultId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**{ [key: string]: boolean; }**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getExternalResultFormatCheck**
> FormatCheckResponse getExternalResultFormatCheck()


### Example

```typescript
import {
    FormattingApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new FormattingApi(configuration);

let externalEditResultId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.getExternalResultFormatCheck(
    externalEditResultId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **externalEditResultId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**FormatCheckResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **listExternalEditResults**
> Array<ExternalEditResultResponse> listExternalEditResults()


### Example

```typescript
import {
    FormattingApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new FormattingApi(configuration);

let documentId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.listExternalEditResults(
    documentId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **documentId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**Array<ExternalEditResultResponse>**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **resolveExternalResultFormatDifference**
> FormatDifferenceResponse resolveExternalResultFormatDifference()


### Example

```typescript
import {
    FormattingApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new FormattingApi(configuration);

let differenceId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.resolveExternalResultFormatDifference(
    differenceId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **differenceId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**FormatDifferenceResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**409** | Conflict |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **runExternalResultAutomaticFormatCheck**
> FormatCheckResponse runExternalResultAutomaticFormatCheck()


### Example

```typescript
import {
    FormattingApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new FormattingApi(configuration);

let externalEditResultId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.runExternalResultAutomaticFormatCheck(
    externalEditResultId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **externalEditResultId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**FormatCheckResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**409** | Conflict |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
