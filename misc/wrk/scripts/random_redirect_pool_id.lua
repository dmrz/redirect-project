local poolIds = { 'pool-a', 'pool-b', 'pool-c' }

function getRandomPoolId()
    return poolIds[math.random( #poolIds )]
end


request = function()
    wrk.headers["X-Redirect-Pool-ID"] = getRandomPoolId()
    return wrk.format(wrk.method, path, wrk.headers, wrk.body)
end