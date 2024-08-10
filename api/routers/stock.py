from fastapi import APIRouter ,  HTTPException  , status
import fastapi as _fastapi
from fastapi.responses import JSONResponse
import schemas as _schemas
import models as _models
import sqlalchemy.orm as _orm
import auth_services as _services
import database as _database
from logger import Logger
from typing import List


# Create an instance of the Logger class
logger_instance = Logger()
# Get a logger for your module
logger = logger_instance.get_logger("stock market api")
router = APIRouter(
    tags=["watchlist"],)


# Create a new watchlist entry
@router.post("/watchlist", response_model=_schemas.Watchlist)
async def create_watchlist(
    watchlist: _schemas.Watchlist,
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),
    db: _orm.Session = _fastapi.Depends(_database.get_db)
):
    logger.info(f"Creating a new watchlist entry for user {user.id} with stock symbol {watchlist.stock_symbol}")

    # Check if the stock already exists in the user's watchlist
    existing_watchlist = db.query(_models.Watchlist).filter(
        _models.Watchlist.user_id == user.id,
        _models.Watchlist.stock_symbol == watchlist.stock_symbol
    ).first()

    if existing_watchlist:
        logger.warning(f"Stock symbol {watchlist.stock_symbol} already exists in watchlist for user {user.id}")
        return JSONResponse(
            content={
                "status": "failed",
                "stock_symbol": watchlist.stock_symbol,
                "stock_name": watchlist.stock_name,
                "message": "Stock already exists in watchlist"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    db_watchlist = _models.Watchlist(**watchlist.dict(), user_id=user.id)
    db.add(db_watchlist)
    db.commit()
    db.refresh(db_watchlist)
    logger.info(f"Created watchlist entry with ID {db_watchlist.id}")

    return JSONResponse(
        content={
            "status": "success",
            "stock_symbol": db_watchlist.stock_symbol,
            "stock_name": db_watchlist.stock_name,
            "message": "Stock added in watchlist"
        },
        status_code=status.HTTP_201_CREATED
    )


# Get all watchlist entries for the current user
@router.get("/watchlist", response_model=List[_schemas.Watchlist])
async def read_watchlist(
    user: _schemas.User =  _fastapi.Depends(_services.get_current_user),
    db:  _orm.Session = _fastapi.Depends(_database.get_db)
):
    logger.info(f"Fetching watchlist entries for user {user.id}")
    watchlists = db.query(_models.Watchlist).filter(_models.Watchlist.user_id == user.id).all()

    res = []
    for watchlist in watchlists:
        
        dictionary = {
            "id": watchlist.id,
            "stock_symbol": watchlist.stock_symbol,
            "stock_name": watchlist.stock_name,
            
        }
        res.append(dictionary)
      
    if not watchlists:
        logger.info(f"No watchlist entries found for user {user.id}")
        return JSONResponse(
            content={
                "status": "success",
                "message": "No watchlist entries found",
                "data": None
            },
            status_code=status.HTTP_200_OK
        )

    logger.info(f"Found {len(watchlists)} watchlist entries for user {user.id}")
    
    return JSONResponse(
            content={
                "status": "success",
                "message": "Watchlist entries retrieved successfully",
                "data": res
            },
            status_code=status.HTTP_200_OK
        )
 

# Update a watchlist entry
@router.put("/watchlist/{watchlist_id}", response_model=_schemas.Watchlist)
async def update_watchlist(
    watchlist_id: int,
    watchlist: _schemas.Watchlist,
    user: _schemas.User =  _fastapi.Depends(_services.get_current_user),
    db: _orm.Session = _fastapi.Depends(_database.get_db)
):
    # Fetch the existing watchlist entry
    db_watchlist = db.query(_models.Watchlist).filter(
        _models.Watchlist.id == watchlist_id, 
        _models.Watchlist.user_id == user.id
    ).first()
    
    if db_watchlist is None:
        logger.error(f"Watchlist entry with ID {watchlist_id} not found for user {user.id}")
        return JSONResponse(
            content={
                "status": "failed",
                "message": "Enter a valid watchlist ID",
                "data": None
            },
            status_code=status.HTTP_404_NOT_FOUND
        )

    # Update the watchlist entry
    db_watchlist.stock_symbol = watchlist.stock_symbol
    db_watchlist.stock_name = watchlist.stock_name
    db.commit()
    db.refresh(db_watchlist)

    logger.info(f"Updated watchlist entry with ID {watchlist_id}")
    
    # Return the updated entry along with status and message
    return JSONResponse(
            content={
                "status": "success",
                "message": "Watchlist entry updated successfully",
                "data": { "stock_name": db_watchlist.stock_symbol,
                          "stock_symbol": db_watchlist.stock_name
                        }
            },
            status_code=status.HTTP_200_OK
        )
 
# Delete a watchlist entry
@router.delete("/watchlist/{watchlist_id}", response_model=_schemas.Watchlist)
async def delete_watchlist(
    watchlist_id: int,
    user: _schemas.User =  _fastapi.Depends(_services.get_current_user),
    db:  _orm.Session = _fastapi.Depends(_database.get_db)
):
    # Fetch the existing watchlist entry
    db_watchlist = db.query(_models.Watchlist).filter(
        _models.Watchlist.id == watchlist_id,
        _models.Watchlist.user_id == user.id
    ).first()
    
    if db_watchlist is None:
        logger.error(f"Watchlist entry with ID {watchlist_id} not found for user {user.id}")
        return JSONResponse(
            content={
                "status": "failed",
                "message": "Watchlist entry not found",
                "data": None
            },
            status_code=status.HTTP_404_NOT_FOUND
        )

    # Delete the watchlist entry
    db.delete(db_watchlist)
    db.commit()
    
    logger.info(f"Deleted watchlist entry with ID {watchlist_id}")
    
    # Return a response with status and message


    return JSONResponse(
            content={
                "status": "success",
                "message": "Watchlist entry deleted successfully",
                "data": { "stock_name": db_watchlist.stock_symbol,
                          "stock_symbol": db_watchlist.stock_name
                        }
            },
            status_code=status.HTTP_200_OK
        )
    