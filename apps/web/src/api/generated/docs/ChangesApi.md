# ChangesApi

All URIs are relative to *http://localhost*

|Method | HTTP request | Description|
|------------- | ------------- | -------------|
|[**createChangeComment**](#createchangecomment) | **POST** /api/v1/changes/{change_request_id}/comments | Create Change Comment|
|[**createChangeProposal**](#createchangeproposal) | **POST** /api/v1/changes/{change_request_id}/proposals | Create Change Proposal|
|[**createChangeRequest**](#createchangerequest) | **POST** /api/v1/changes | Create Change Request|
|[**decideChangeProposal**](#decidechangeproposal) | **PATCH** /api/v1/changes/{change_request_id}/proposals/{proposal_id}/decision | Decide Change Proposal|
|[**getChangeRequest**](#getchangerequest) | **GET** /api/v1/changes/{change_request_id} | Get Change Request|
|[**listChangeComments**](#listchangecomments) | **GET** /api/v1/changes/{change_request_id}/comments | List Change Comments|
|[**listChangeRequests**](#listchangerequests) | **GET** /api/v1/changes | List Change Requests|
|[**transitionChangeComment**](#transitionchangecomment) | **PATCH** /api/v1/changes/{change_request_id}/comments/{comment_id}/status | Transition Change Comment|
|[**transitionChangeRequest**](#transitionchangerequest) | **PATCH** /api/v1/changes/{change_request_id}/status | Transition Change Request|

# **createChangeComment**
> ChangeCommentResponse createChangeComment(changeCommentCreate)


### Example

```typescript
import {
    ChangesApi,
    Configuration,
    ChangeCommentCreate
} from './api';

const configuration = new Configuration();
const apiInstance = new ChangesApi(configuration);

let changeRequestId: string; // (default to undefined)
let changeCommentCreate: ChangeCommentCreate; //
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.createChangeComment(
    changeRequestId,
    changeCommentCreate,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **changeCommentCreate** | **ChangeCommentCreate**|  | |
| **changeRequestId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**ChangeCommentResponse**

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
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **createChangeProposal**
> ChangeProposalResponse createChangeProposal(changeProposalCreate)


### Example

```typescript
import {
    ChangesApi,
    Configuration,
    ChangeProposalCreate
} from './api';

const configuration = new Configuration();
const apiInstance = new ChangesApi(configuration);

let changeRequestId: string; // (default to undefined)
let changeProposalCreate: ChangeProposalCreate; //
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.createChangeProposal(
    changeRequestId,
    changeProposalCreate,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **changeProposalCreate** | **ChangeProposalCreate**|  | |
| **changeRequestId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**ChangeProposalResponse**

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
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **createChangeRequest**
> ChangeRequestResponse createChangeRequest(changeRequestCreate)


### Example

```typescript
import {
    ChangesApi,
    Configuration,
    ChangeRequestCreate
} from './api';

const configuration = new Configuration();
const apiInstance = new ChangesApi(configuration);

let changeRequestCreate: ChangeRequestCreate; //
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.createChangeRequest(
    changeRequestCreate,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **changeRequestCreate** | **ChangeRequestCreate**|  | |
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**ChangeRequestResponse**

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
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **decideChangeProposal**
> ChangeProposalResponse decideChangeProposal(changeProposalDecision)


### Example

```typescript
import {
    ChangesApi,
    Configuration,
    ChangeProposalDecision
} from './api';

const configuration = new Configuration();
const apiInstance = new ChangesApi(configuration);

let changeRequestId: string; // (default to undefined)
let proposalId: string; // (default to undefined)
let changeProposalDecision: ChangeProposalDecision; //
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.decideChangeProposal(
    changeRequestId,
    proposalId,
    changeProposalDecision,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **changeProposalDecision** | **ChangeProposalDecision**|  | |
| **changeRequestId** | [**string**] |  | defaults to undefined|
| **proposalId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**ChangeProposalResponse**

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

# **getChangeRequest**
> ChangeRequestResponse getChangeRequest()


### Example

```typescript
import {
    ChangesApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new ChangesApi(configuration);

let changeRequestId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.getChangeRequest(
    changeRequestId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **changeRequestId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**ChangeRequestResponse**

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

# **listChangeComments**
> Array<ChangeCommentResponse> listChangeComments()


### Example

```typescript
import {
    ChangesApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new ChangesApi(configuration);

let changeRequestId: string; // (default to undefined)
let assigneeId: string; // (optional) (default to undefined)
let status: ChangeCommentStatus; // (optional) (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.listChangeComments(
    changeRequestId,
    assigneeId,
    status,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **changeRequestId** | [**string**] |  | defaults to undefined|
| **assigneeId** | [**string**] |  | (optional) defaults to undefined|
| **status** | **ChangeCommentStatus** |  | (optional) defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**Array<ChangeCommentResponse>**

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

# **listChangeRequests**
> Array<ChangeRequestResponse> listChangeRequests()


### Example

```typescript
import {
    ChangesApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new ChangesApi(configuration);

let documentId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.listChangeRequests(
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

**Array<ChangeRequestResponse>**

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
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **transitionChangeComment**
> ChangeCommentResponse transitionChangeComment(changeCommentTransition)


### Example

```typescript
import {
    ChangesApi,
    Configuration,
    ChangeCommentTransition
} from './api';

const configuration = new Configuration();
const apiInstance = new ChangesApi(configuration);

let changeRequestId: string; // (default to undefined)
let commentId: string; // (default to undefined)
let changeCommentTransition: ChangeCommentTransition; //
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.transitionChangeComment(
    changeRequestId,
    commentId,
    changeCommentTransition,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **changeCommentTransition** | **ChangeCommentTransition**|  | |
| **changeRequestId** | [**string**] |  | defaults to undefined|
| **commentId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**ChangeCommentResponse**

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
|**403** | Forbidden |  -  |
|**404** | Not Found |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **transitionChangeRequest**
> ChangeRequestResponse transitionChangeRequest(changeRequestTransition)


### Example

```typescript
import {
    ChangesApi,
    Configuration,
    ChangeRequestTransition
} from './api';

const configuration = new Configuration();
const apiInstance = new ChangesApi(configuration);

let changeRequestId: string; // (default to undefined)
let changeRequestTransition: ChangeRequestTransition; //
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.transitionChangeRequest(
    changeRequestId,
    changeRequestTransition,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **changeRequestTransition** | **ChangeRequestTransition**|  | |
| **changeRequestId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**ChangeRequestResponse**

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
