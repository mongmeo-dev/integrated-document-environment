# LatexApi

All URIs are relative to *http://localhost*

|Method | HTTP request | Description|
|------------- | ------------- | -------------|
|[**createLatexSourceRevision**](#createlatexsourcerevision) | **POST** /api/v1/documents/{document_id}/latex/revisions | Create Latex Source Revision|
|[**getLatexBundle**](#getlatexbundle) | **GET** /api/v1/documents/{document_id}/latex/bundle | Get Latex Bundle|
|[**getLatexPreview**](#getlatexpreview) | **GET** /api/v1/documents/{document_id}/latex/preview | Get Latex Preview|
|[**getLatexProject**](#getlatexproject) | **GET** /api/v1/documents/{document_id}/latex | Get Latex Project|
|[**reviewLatexConversion**](#reviewlatexconversion) | **POST** /api/v1/documents/{document_id}/latex/conversion-reviews | Review Latex Conversion|

# **createLatexSourceRevision**
> LatexProjectResponse createLatexSourceRevision(latexSourceRevisionCreate)


### Example

```typescript
import {
    LatexApi,
    Configuration,
    LatexSourceRevisionCreate
} from './api';

const configuration = new Configuration();
const apiInstance = new LatexApi(configuration);

let documentId: string; // (default to undefined)
let latexSourceRevisionCreate: LatexSourceRevisionCreate; //
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.createLatexSourceRevision(
    documentId,
    latexSourceRevisionCreate,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **latexSourceRevisionCreate** | **LatexSourceRevisionCreate**|  | |
| **documentId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**LatexProjectResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**201** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**409** | Conflict |  -  |
|**422** | Unprocessable Content |  -  |
|**503** | Service Unavailable |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getLatexBundle**
> any getLatexBundle()


### Example

```typescript
import {
    LatexApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new LatexApi(configuration);

let documentId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.getLatexBundle(
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

**any**

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
|**422** | Unprocessable Content |  -  |
|**503** | Service Unavailable |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getLatexPreview**
> any getLatexPreview()


### Example

```typescript
import {
    LatexApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new LatexApi(configuration);

let documentId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.getLatexPreview(
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

**any**

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
|**422** | Unprocessable Content |  -  |
|**503** | Service Unavailable |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getLatexProject**
> LatexProjectResponse getLatexProject()


### Example

```typescript
import {
    LatexApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new LatexApi(configuration);

let documentId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.getLatexProject(
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

**LatexProjectResponse**

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
|**422** | Unprocessable Content |  -  |
|**503** | Service Unavailable |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **reviewLatexConversion**
> LatexProjectResponse reviewLatexConversion(conversionReviewCreate)


### Example

```typescript
import {
    LatexApi,
    Configuration,
    ConversionReviewCreate
} from './api';

const configuration = new Configuration();
const apiInstance = new LatexApi(configuration);

let documentId: string; // (default to undefined)
let conversionReviewCreate: ConversionReviewCreate; //
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.reviewLatexConversion(
    documentId,
    conversionReviewCreate,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **conversionReviewCreate** | **ConversionReviewCreate**|  | |
| **documentId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**LatexProjectResponse**

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
|**422** | Unprocessable Content |  -  |
|**503** | Service Unavailable |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
